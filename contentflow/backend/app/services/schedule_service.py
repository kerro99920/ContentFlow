import uuid
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

_scheduler: AsyncIOScheduler | None = None


def _get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


async def execute_scheduled_task(scheduled_task_id: str) -> None:
    from app.database import async_session
    from app.models.schedule import ScheduledTask, ScheduledTaskRun
    from app.models.brand_profile import BrandProfile
    from app.models.content import Content, GenerationTask
    from app.services.generation_service import _do_generation
    from app.services.email_service import send_email, build_content_email
    from app.models.user import User

    task_uuid = uuid.UUID(scheduled_task_id)

    async with async_session() as db:
        task = await db.get(ScheduledTask, task_uuid)
        if not task or not task.is_active:
            return

        run = ScheduledTaskRun(scheduled_task_id=task_uuid)
        db.add(run)
        await db.flush()
        await db.refresh(run)
        run_id = run.id

        custom_system_prompt = None
        if task.brand_profile_id:
            bp = await db.get(BrandProfile, task.brand_profile_id)
            if bp:
                custom_system_prompt = bp.system_prompt

        user = await db.get(User, task.user_id)
        user_email = user.email if user else None

        generated_ids = []
        error_msg = None

        try:
            for platform in task.platforms:
                gen_task = GenerationTask(
                    user_id=task.user_id,
                    source_material=task.source_material,
                    platform=platform,
                    brand_tone=task.brand_tone,
                )
                db.add(gen_task)
                await db.flush()
                await db.refresh(gen_task)

                await _do_generation(
                    db, gen_task.id, task.user_id,
                    task.source_material, platform, task.brand_tone,
                    custom_system_prompt,
                )
                await db.refresh(gen_task)
                if gen_task.content_id:
                    generated_ids.append(str(gen_task.content_id))

            task.last_run_at = datetime.now(timezone.utc)
            run.status = "completed"
            run.finished_at = datetime.now(timezone.utc)
            run.generated_content_ids = generated_ids
            await db.commit()

        except Exception as e:
            error_msg = str(e)
            run.status = "failed"
            run.finished_at = datetime.now(timezone.utc)
            run.error_message = error_msg
            await db.commit()
            return

        # 发送邮件通知
        if user_email and generated_ids:
            content_dicts = []
            for cid in generated_ids:
                c = await db.get(Content, uuid.UUID(cid))
                if c:
                    content_dicts.append({"platform": c.platform, "title": c.title, "body": c.body or ""})
            if content_dicts:
                html = build_content_email(content_dicts, task.name)
                await send_email(user_email, f"ContentFlow - {task.name} 已完成", html)


async def _add_job_to_scheduler(task_id: str, cron_expression: str) -> None:
    scheduler = _get_scheduler()
    parts = cron_expression.strip().split()
    if len(parts) != 5:
        return
    minute, hour, day, month, day_of_week = parts
    trigger = CronTrigger(
        minute=minute, hour=hour, day=day,
        month=month, day_of_week=day_of_week,
    )
    job_id = f"scheduled_task_{task_id}"
    # 移除旧任务（如果存在）
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    scheduler.add_job(
        execute_scheduled_task,
        trigger=trigger,
        args=[task_id],
        id=job_id,
        replace_existing=True,
    )


async def remove_job_from_scheduler(task_id: str) -> None:
    scheduler = _get_scheduler()
    job_id = f"scheduled_task_{task_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


async def init_scheduler() -> None:
    from app.database import async_session
    from app.models.schedule import ScheduledTask

    scheduler = _get_scheduler()
    if not scheduler.running:
        scheduler.start()

    # 从数据库加载活跃任务
    async with async_session() as db:
        result = await db.execute(select(ScheduledTask).where(ScheduledTask.is_active == True))
        tasks = result.scalars().all()
        for task in tasks:
            await _add_job_to_scheduler(str(task.id), task.cron_expression)


async def register_task(task_id: str, cron_expression: str) -> None:
    await _add_job_to_scheduler(task_id, cron_expression)
