import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.content import Content, GenerationTask
from app.services.ai_service import generate_content
from app.services.usage_service import increment_usage
from app.prompts.registry import get_prompt_builders, get_validator


async def run_generation(
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    source_material: str,
    platform: str,
    brand_tone: str,
    custom_system_prompt: str | None = None,
) -> None:
    from app.database import async_session
    async with async_session() as db:
        await _do_generation(db, task_id, user_id, source_material, platform, brand_tone, custom_system_prompt)


async def _do_generation(
    db: AsyncSession,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    source_material: str,
    platform: str,
    brand_tone: str,
    custom_system_prompt: str | None = None,
) -> None:
    task = await db.get(GenerationTask, task_id)
    task.status = "running"
    await db.commit()

    try:
        build_system, build_user = get_prompt_builders(platform)
        if custom_system_prompt:
            system_prompt = custom_system_prompt
        else:
            system_prompt = build_system(brand_tone)
        user_prompt = build_user(source_material)
        validator = get_validator(platform)

        result = None
        for attempt in range(3):
            result = await generate_content(system_prompt, user_prompt)
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
            body=result.get("body") or result.get("subtitle_text"),
            tags=result.get("tags") or result.get("keywords"),
            metadata_=result,
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
        # 截断错误信息，避免泄露敏感信息
        error_msg = str(e)
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        task.error_message = error_msg
        await db.commit()
