import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.content import Content, GenerationTask
from app.schemas.content import (
    GenerateRequest, GenerateResponse, TaskStatusResponse,
    ContentResponse, ContentListResponse,
    BatchGenerateRequest, BatchGenerateResponse, ContentUpdateRequest,
)
from app.services.usage_service import check_quota
from app.services.generation_service import run_generation

router = APIRouter(prefix="/api/content", tags=["content"])

@router.post("/generate", response_model=GenerateResponse, status_code=202)
async def generate(
    req: GenerateRequest,
    bg: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not await check_quota(db, user.id):
        raise HTTPException(
            status_code=403,
            detail={"code": "QUOTA_EXCEEDED", "message": "本月免费额度已用完"},
        )

    task = GenerationTask(
        user_id=user.id,
        source_material=req.source_material,
        platform=req.platform,
        brand_tone=req.brand_tone,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    bg.add_task(run_generation, task.id, user.id, req.source_material, req.platform, req.brand_tone)

    return GenerateResponse(task_id=str(task.id))

@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = await db.get(GenerationTask, uuid.UUID(task_id))
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusResponse(
        task_id=str(task.id),
        status=task.status,
        content_id=str(task.content_id) if task.content_id else None,
        error_message=task.error_message,
    )

@router.get("", response_model=ContentListResponse)
async def list_content(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    offset = (page - 1) * page_size
    query = select(Content).where(Content.user_id == user.id).order_by(Content.created_at.desc())
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()
    result = await db.execute(query.offset(offset).limit(page_size))
    items = [
        ContentResponse(
            id=str(c.id), platform=c.platform, title=c.title, body=c.body,
            tags=c.tags, metadata=c.metadata_, brand_tone=c.brand_tone,
            status=c.status, created_at=c.created_at.isoformat(),
        )
        for c in result.scalars()
    ]
    return ContentListResponse(items=items, total=total, page=page, page_size=page_size)

@router.post("/generate-batch", response_model=BatchGenerateResponse, status_code=202)
async def generate_batch(
    req: BatchGenerateRequest,
    bg: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 检查配额是否够所有平台使用
    from app.models.usage import UsageRecord
    from app.config import settings as cfg
    from sqlalchemy import select as sa_select
    from datetime import datetime, timezone
    period = datetime.now(timezone.utc).strftime("%Y-%m")
    result = await db.execute(
        sa_select(UsageRecord).where(UsageRecord.user_id == user.id, UsageRecord.period == period)
    )
    record = result.scalar_one_or_none()
    current_count = record.generation_count if record else 0
    remaining = cfg.free_monthly_quota - current_count
    if remaining < len(req.platforms):
        raise HTTPException(
            status_code=403,
            detail={"code": "QUOTA_EXCEEDED", "message": "本月免费额度不足"},
        )

    # 获取品牌自定义提示词
    custom_system_prompt = None
    if req.brand_profile_id:
        from app.models.brand_profile import BrandProfile
        bp = await db.get(BrandProfile, uuid.UUID(req.brand_profile_id))
        if bp and bp.user_id == user.id:
            custom_system_prompt = bp.system_prompt

    task_ids: dict[str, str] = {}
    for platform in req.platforms:
        task = GenerationTask(
            user_id=user.id,
            source_material=req.source_material,
            platform=platform,
            brand_tone=req.brand_tone,
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)
        bg.add_task(run_generation, task.id, user.id, req.source_material, platform, req.brand_tone, custom_system_prompt)
        task_ids[platform] = str(task.id)

    await db.commit()
    return BatchGenerateResponse(task_ids=task_ids)

@router.get("/calendar")
async def get_calendar(
    month: str = Query(..., description="格式 YYYY-MM"),
    platform: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from sqlalchemy import extract
    try:
        year, mon = month.split("-")
        year, mon = int(year), int(mon)
    except ValueError:
        raise HTTPException(status_code=400, detail="month 格式应为 YYYY-MM")

    query = select(Content).where(
        Content.user_id == user.id,
        extract("year", Content.created_at) == year,
        extract("month", Content.created_at) == mon,
    )
    if platform:
        query = query.where(Content.platform == platform)
    if status:
        query = query.where(Content.status == status)

    result = await db.execute(query.order_by(Content.created_at))
    contents = result.scalars().all()

    days: dict[str, list] = {}
    for c in contents:
        day_key = c.created_at.strftime("%Y-%m-%d")
        if day_key not in days:
            days[day_key] = []
        days[day_key].append(ContentResponse(
            id=str(c.id), platform=c.platform, title=c.title, body=c.body,
            tags=c.tags, metadata=c.metadata_, brand_tone=c.brand_tone,
            status=c.status, created_at=c.created_at.isoformat(),
        ))

    return {"month": month, "days": days}

@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: str,
    req: ContentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await db.get(Content, uuid.UUID(content_id))
    if not content or content.user_id != user.id:
        raise HTTPException(status_code=404, detail="Content not found")
    if req.title is not None:
        content.title = req.title
    if req.body is not None:
        content.body = req.body
    if req.tags is not None:
        content.tags = req.tags
    if req.status is not None:
        content.status = req.status
    await db.commit()
    await db.refresh(content)
    return ContentResponse(
        id=str(content.id), platform=content.platform, title=content.title,
        body=content.body, tags=content.tags, metadata=content.metadata_,
        brand_tone=content.brand_tone, status=content.status,
        created_at=content.created_at.isoformat(),
    )

@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await db.get(Content, uuid.UUID(content_id))
    if not content or content.user_id != user.id:
        raise HTTPException(status_code=404, detail="Content not found")
    return ContentResponse(
        id=str(content.id), platform=content.platform, title=content.title,
        body=content.body, tags=content.tags, metadata=content.metadata_,
        brand_tone=content.brand_tone, status=content.status,
        created_at=content.created_at.isoformat(),
    )

@router.delete("/{content_id}", status_code=204)
async def delete_content(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await db.get(Content, uuid.UUID(content_id))
    if not content or content.user_id != user.id:
        raise HTTPException(status_code=404, detail="Content not found")
    await db.delete(content)
    await db.commit()
