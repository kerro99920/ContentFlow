import pytest
from app.prompts.registry import get_prompt_builders, get_validator, PLATFORM_PROMPTS

def test_all_platforms_registered():
    assert set(PLATFORM_PROMPTS.keys()) == {"xiaohongshu", "douyin", "wechat", "blog"}

@pytest.mark.parametrize("platform", ["xiaohongshu", "douyin", "wechat", "blog"])
def test_prompt_builders_return_strings(platform):
    build_sys, build_user = get_prompt_builders(platform)
    sys_prompt = build_sys("casual")
    user_prompt = build_user("test material")
    assert isinstance(sys_prompt, str) and len(sys_prompt) > 50
    assert "test material" in user_prompt

def test_xiaohongshu_validator():
    v = get_validator("xiaohongshu")
    assert v({"title": "短标题", "body": "内容", "tags": ["t"]}) is True
    assert v({"title": "x" * 21, "body": "内容", "tags": ["t"]}) is False

def test_douyin_validator():
    v = get_validator("douyin")
    assert v({"hook": "钩子", "script_sections": [{"time": "0-3s"}]}) is True
    assert v({"script_sections": []}) is False

def test_wechat_validator():
    v = get_validator("wechat")
    assert v({"title": "标题", "body": "x" * 800}) is True
    assert v({"title": "标题", "body": "短"}) is False

def test_blog_validator():
    v = get_validator("blog")
    assert v({"keywords": ["k"], "meta_description": "desc"}) is True
    assert v({"keywords": ["k"]}) is False

def test_unknown_platform_raises():
    with pytest.raises(ValueError):
        get_prompt_builders("unknown")
