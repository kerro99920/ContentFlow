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
