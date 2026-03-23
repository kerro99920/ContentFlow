from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.usage import UsageRecord
from app.config import settings
import uuid

def _current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")

async def _get_or_create_record(db: AsyncSession, user_id: uuid.UUID) -> UsageRecord:
    period = _current_period()
    result = await db.execute(
        select(UsageRecord).where(
            UsageRecord.user_id == user_id,
            UsageRecord.period == period,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        record = UsageRecord(user_id=user_id, period=period, generation_count=0)
        db.add(record)
        await db.flush()
    return record

async def check_quota(db: AsyncSession, user_id: uuid.UUID) -> bool:
    record = await _get_or_create_record(db, user_id)
    return record.generation_count < settings.free_monthly_quota

async def increment_usage(db: AsyncSession, user_id: uuid.UUID) -> None:
    record = await _get_or_create_record(db, user_id)
    record.generation_count += 1
    await db.commit()

async def get_usage(db: AsyncSession, user_id: uuid.UUID) -> dict:
    record = await _get_or_create_record(db, user_id)
    return {
        "period": record.period,
        "generation_count": record.generation_count,
        "quota": settings.free_monthly_quota,
    }
