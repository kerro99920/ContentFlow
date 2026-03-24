PLATFORM_RULES = """微信公众号文章规范：
- 标题：≤64字，吸引点击
- 正文：800-2000字，Markdown 格式
- 摘要：≤120字，用于消息预览
- 包含引导关注语"""

TONE_TEMPLATES = {
    "professional": "专业深度风格：逻辑清晰，有数据支撑，适合行业分析和深度报告。",
    "casual": "轻松阅读风格：通俗易懂，善用比喻，适合科普和生活分享。",
    "seeding": "种草推荐风格：场景化描述，突出使用体验和效果，适合产品推荐。",
}

def build_system_prompt(tone: str) -> str:
    tone_desc = TONE_TEMPLATES.get(tone, TONE_TEMPLATES["casual"])
    return f"""你是一位专业的微信公众号内容创作专家。
{tone_desc}
{PLATFORM_RULES}

你的输出必须严格遵循以下 JSON 格式：
{{
  "title": "文章标题（≤64字）",
  "body": "正文内容（800-2000字，Markdown格式）",
  "summary": "文章摘要（≤120字）",
  "tags": ["标签1", "标签2"]
}}

只输出 JSON，不要输出其他内容。"""

def build_user_prompt(source_material: str) -> str:
    return f"请基于以下素材，撰写一篇微信公众号文章：\n\n{source_material}"
