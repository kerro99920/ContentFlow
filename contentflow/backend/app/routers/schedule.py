import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.deps import get_current_user, parse_uuid
from app.models.user import User
from app.models.schedule import ScheduledTask
from app.schemas.schedule import ScheduleCreateRequest, ScheduleUpdateRequest, ScheduleResponse

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


def _to_response(t: ScheduledTask) -> ScheduleResponse:
    return ScheduleResponse(
        id=str(t.id),
        name=t.name,
        cron_expression=t.cron_expression,
        source_material=t.source_material,
        platforms=t.platforms,
        brand_tone=t.brand_tone,
        is_active=t.is_active,
        last_run_at=t.last_run_at.isoformat() if t.last_run_at else None,
        created_at=t.created_at.isoformat(),
    )


@router.post("", response_model=ScheduleResponse, status_code=201)
async def create_schedule(
    req: ScheduleCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    brand_profile_id = parse_uuid(req.brand_profile_id) if req.brand_profile_id else None
    task = ScheduledTask(
        user_id=user.id,
        name=req.name,
        cron_expression=req.cron_expression,
        source_material=req.source_material,
        platforms=req.platforms,
        brand_tone=req.brand_tone,
        brand_profile_id=brand_profile_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    try:
        from app.services.schedule_service import register_task
        await register_task(str(task.id), task.cron_expression)
    except Exception:
        pass

    return _to_response(task)


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(ScheduledTask).where(ScheduledTask.user_id == user.id))
    return [_to_response(t) for t in result.scalars()]


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: str,
    req: ScheduleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = await db.get(ScheduledTask, parse_uuid(schedule_id))
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "定时任务不存在"})
    if req.name is not None:
        task.name = req.name
    if req.cron_expression is not None:
        task.cron_expression = req.cron_expression
    if req.source_material is not None:
        task.source_material = req.source_material
    if req.platforms is not None:
        task.platforms = req.platforms
    if req.brand_tone is not None:
        task.brand_tone = req.brand_tone
    if req.is_active is not None:
        task.is_active = req.is_active
    await db.commit()
    await db.refresh(task)

    try:
        from app.services.schedule_service import register_task, remove_job_from_scheduler
        if task.is_active:
            await register_task(str(task.id), task.cron_expression)
        else:
            await remove_job_from_scheduler(str(task.id))
    except Exception:
        pass

    return _to_response(task)


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = await db.get(ScheduledTask, parse_uuid(schedule_id))
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "定时任务不存在"})
    try:
        from app.services.schedule_service import remove_job_from_scheduler
        await remove_job_from_scheduler(str(task.id))
    except Exception:
        pass
    await db.delete(task)
    await db.commit()


@router.post("/{schedule_id}/run", status_code=202)
async def manual_run(
    schedule_id: str,
    bg: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = await db.get(ScheduledTask, parse_uuid(schedule_id))
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "定时任务不存在"})
    from app.services.schedule_service import execute_scheduled_task
    bg.add_task(execute_scheduled_task, schedule_id)
    return {"status": "triggered"}
