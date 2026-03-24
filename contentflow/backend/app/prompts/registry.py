from app.prompts import xiaohongshu, douyin, wechat, blog

PLATFORM_PROMPTS = {
    "xiaohongshu": (xiaohongshu.build_system_prompt, xiaohongshu.build_user_prompt),
    "douyin": (douyin.build_system_prompt, douyin.build_user_prompt),
    "wechat": (wechat.build_system_prompt, wechat.build_user_prompt),
    "blog": (blog.build_system_prompt, blog.build_user_prompt),
}

VALIDATORS = {
    "xiaohongshu": lambda d: (
        len(d.get("title", "")) <= 20
        and len(d.get("body", "")) <= 1000
        and isinstance(d.get("tags"), list)
    ),
    "douyin": lambda d: (
        isinstance(d.get("script_sections"), list)
        and len(d.get("script_sections", [])) > 0
        and "hook" in d
    ),
    "wechat": lambda d: (
        len(d.get("title", "")) <= 64
        and 800 <= len(d.get("body", "")) <= 2500
    ),
    "blog": lambda d: (
        isinstance(d.get("keywords"), list)
        and "meta_description" in d
    ),
}

def get_prompt_builders(platform: str):
    if platform not in PLATFORM_PROMPTS:
        raise ValueError(f"不支持的平台: {platform}")
    return PLATFORM_PROMPTS[platform]

def get_validator(platform: str):
    return VALIDATORS.get(platform, lambda _: True)
