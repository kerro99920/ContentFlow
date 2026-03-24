import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_batch_generate(authed_client: AsyncClient):
    with patch("app.routers.content.run_generation", new_callable=AsyncMock):
        resp = await authed_client.post("/api/content/generate-batch", json={
            "source_material": "test material", "platforms": ["xiaohongshu", "douyin"], "brand_tone": "casual",
        })
    assert resp.status_code == 202
    assert "xiaohongshu" in resp.json()["task_ids"]
    assert "douyin" in resp.json()["task_ids"]

@pytest.mark.asyncio
async def test_batch_exceeds_quota(authed_client: AsyncClient, db_session, test_user):
    from app.services.usage_service import increment_usage
    for _ in range(9):
        await increment_usage(db_session, test_user.id)
    resp = await authed_client.post("/api/content/generate-batch", json={
        "source_material": "test", "platforms": ["xiaohongshu", "douyin"], "brand_tone": "casual",
    })
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_update_content(authed_client: AsyncClient, db_session, test_user):
    from app.models.content import Content
    c = Content(user_id=test_user.id, source_material="s", platform="xiaohongshu", title="old", status="draft")
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    resp = await authed_client.put(f"/api/content/{c.id}", json={"title": "new", "status": "approved"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "new"
    assert resp.json()["status"] == "approved"

@pytest.mark.asyncio
async def test_calendar(authed_client: AsyncClient):
    resp = await authed_client.get("/api/content/calendar?month=2026-03")
    assert resp.status_code == 200
    assert "month" in resp.json()
    assert "days" in resp.json()
