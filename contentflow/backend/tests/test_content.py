import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_generate_content(authed_client: AsyncClient):
    with patch("app.routers.content.run_generation", new_callable=AsyncMock):
        resp = await authed_client.post("/api/content/generate", json={
            "source_material": "测试素材",
            "platform": "xiaohongshu",
            "brand_tone": "casual",
        })
    assert resp.status_code == 202
    assert "task_id" in resp.json()

@pytest.mark.asyncio
async def test_generate_exceeds_quota(authed_client: AsyncClient, db_session, test_user):
    from app.services.usage_service import increment_usage
    for _ in range(10):
        await increment_usage(db_session, test_user.id)

    resp = await authed_client.post("/api/content/generate", json={
        "source_material": "测试", "platform": "xiaohongshu", "brand_tone": "casual",
    })
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "QUOTA_EXCEEDED"

@pytest.mark.asyncio
async def test_list_content(authed_client: AsyncClient):
    resp = await authed_client.get("/api/content")
    assert resp.status_code == 200
    assert "items" in resp.json()

@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    resp = await client.get("/api/content")
    assert resp.status_code in [401, 403]
