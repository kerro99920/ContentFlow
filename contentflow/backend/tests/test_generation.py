import pytest
from unittest.mock import AsyncMock, patch
from app.services.generation_service import _do_generation
from app.models.content import GenerationTask

MOCK_AI_RESPONSE = {
    "title": "测试标题",
    "body": "测试正文内容",
    "tags": ["测试", "AI"],
    "cover_text": "封面文案",
}

@pytest.mark.asyncio
@patch("app.services.generation_service.generate_content", new_callable=AsyncMock)
async def test_generation_creates_content(mock_ai, db_session, test_user):
    mock_ai.return_value = MOCK_AI_RESPONSE

    task = GenerationTask(
        user_id=test_user.id,
        source_material="测试素材",
        platform="xiaohongshu",
        brand_tone="casual",
    )
    db_session.add(task)
    await db_session.commit()

    await _do_generation(
        db_session, task.id, test_user.id,
        "测试素材", "xiaohongshu", "casual"
    )

    await db_session.refresh(task)
    assert task.status == "completed"
    assert task.content_id is not None
