import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.content import Content, GenerationTask
from app.services.ai_service import generate_content
from app.services.usage_service import increment_usage
from app.prompts.xiaohongshu import build_system_prompt, build_user_prompt

VALIDATORS = {
    "xiaohongshu": lambda d: (
        len(d.get("title", "")) <= 20
        and len(d.get("body", "")) <= 1000
        and isinstance(d.get("tags"), list)
    ),
}

async def run_generation(
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    source_material: str,
    platform: str,
    brand_tone: str,
) -> None:
    from app.database import async_session
    async with async_session() as db:
        await _do_generation(db, task_id, user_id, source_material, platform, brand_tone)

async def _do_generation(
    db: AsyncSession,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    source_material: str,
    platform: str,
    brand_tone: str,
) -> None:
    task = await db.get(GenerationTask, task_id)
    task.status = "running"
    await db.commit()

    try:
        system_prompt = build_system_prompt(brand_tone)
        user_prompt = build_user_prompt(source_material)

        result = None
        for attempt in range(3):
            result = await generate_content(system_prompt, user_prompt)
            validator = VALIDATORS.get(platform, lambda _: True)
            if validator(result):
                break
        else:
            task.status = "failed"
            task.error_message = "内容校验未通过，请重试"
            await db.commit()
            return

        content = Content(
            user_id=user_id,
            source_material=source_material,
            platform=platform,
            title=result.get("title"),
            body=result.get("body"),
            tags=result.get("tags"),
            metadata_={"cover_text": result.get("cover_text")},
            brand_tone=brand_tone,
            status="draft",
        )
        db.add(content)
        await db.flush()

        task.status = "completed"
        task.content_id = content.id
        await increment_usage(db, user_id)
        await db.commit()

    except Exception as e:
        task.status = "failed"
        task.error_message = str(e)
        await db.commit()
