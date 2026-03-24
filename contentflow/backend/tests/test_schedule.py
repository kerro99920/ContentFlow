import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_schedule(authed_client: AsyncClient):
    resp = await authed_client.post("/api/schedules", json={
        "name": "每日生成", "cron_expression": "0 9 * * *",
        "source_material": "每日咖啡推荐", "platforms": ["xiaohongshu"], "brand_tone": "casual",
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "每日生成"
    assert resp.json()["is_active"] is True

@pytest.mark.asyncio
async def test_list_schedules(authed_client: AsyncClient):
    resp = await authed_client.get("/api/schedules")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

@pytest.mark.asyncio
async def test_delete_schedule(authed_client: AsyncClient):
    create = await authed_client.post("/api/schedules", json={
        "name": "temp", "cron_expression": "0 9 * * *",
        "source_material": "x", "platforms": ["xiaohongshu"],
    })
    sid = create.json()["id"]
    resp = await authed_client.delete(f"/api/schedules/{sid}")
    assert resp.status_code == 204
