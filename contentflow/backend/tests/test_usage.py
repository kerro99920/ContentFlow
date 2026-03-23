import pytest
from app.services.usage_service import check_quota, increment_usage, get_usage

@pytest.mark.asyncio
async def test_new_user_has_quota(db_session, test_user):
    has_quota = await check_quota(db_session, test_user.id)
    assert has_quota is True

@pytest.mark.asyncio
async def test_increment_and_check(db_session, test_user):
    for _ in range(10):
        await increment_usage(db_session, test_user.id)
    has_quota = await check_quota(db_session, test_user.id)
    assert has_quota is False

@pytest.mark.asyncio
async def test_get_usage_returns_count(db_session, test_user):
    await increment_usage(db_session, test_user.id)
    await increment_usage(db_session, test_user.id)
    usage = await get_usage(db_session, test_user.id)
    assert usage["generation_count"] == 2
    assert usage["quota"] == 10
