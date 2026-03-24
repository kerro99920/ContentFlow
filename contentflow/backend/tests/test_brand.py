import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

@pytest.mark.asyncio
@patch("app.services.brand_service.generate_content", new_callable=AsyncMock)
async def test_create_brand_profile(mock_ai, authed_client: AsyncClient):
    mock_ai.return_value = {"system_prompt": "mocked prompt"}
    resp = await authed_client.post("/api/brand-profiles", json={
        "name": "测试品牌", "tone_description": "活泼有趣的美妆博主", "industry_keywords": ["美妆", "护肤"],
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "测试品牌"
    assert resp.json()["system_prompt"] == "mocked prompt"

@pytest.mark.asyncio
async def test_list_brand_profiles(authed_client: AsyncClient):
    resp = await authed_client.get("/api/brand-profiles")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
