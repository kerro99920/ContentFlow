from app.services.ai_service import generate_content

BRAND_PROMPT_GENERATOR = """你是一个AI提示词工程专家。用户描述了一个品牌调性，请生成一个系统提示词(system prompt)，
用于指导AI以该品牌调性生成社交媒体内容。

输出JSON格式：
{"system_prompt": "生成的系统提示词"}

只输出JSON。"""

async def generate_brand_system_prompt(tone_description: str, keywords: list[str] | None = None) -> str:
    user_msg = f"品牌调性描述：{tone_description}"
    if keywords:
        user_msg += f"\n行业关键词：{', '.join(keywords)}"
    try:
        result = await generate_content(BRAND_PROMPT_GENERATOR, user_msg)
        return result.get("system_prompt", tone_description)
    except Exception:
        return f"请以以下风格创作内容：{tone_description}"
