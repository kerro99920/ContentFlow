PLATFORM_RULES = """小红书平台规范：
- 标题：≤20字，吸引眼球，可用 emoji
- 正文：≤1000字，口语化，分段清晰，适当使用 emoji
- 话题标签：5-10个，包含热门标签和长尾标签
- 封面文案建议：1句话，适合做图片封面文字"""

TONE_TEMPLATES = {
    "professional": "专业严谨风格：用数据说话，引用权威来源，语气沉稳可信，适合知识科普和行业分析。",
    "casual": "轻松活泼风格：像朋友聊天一样，用口语化表达，多用语气词和 emoji，适合日常分享。",
    "seeding": "种草安利风格：真实使用体验，突出产品亮点和使用场景，有感染力，适合好物推荐。",
}

def build_system_prompt(tone: str) -> str:
    tone_desc = TONE_TEMPLATES.get(tone, TONE_TEMPLATES["casual"])
    return f"""你是一位专业的小红书内容创作专家。
{tone_desc}
{PLATFORM_RULES}

你的输出必须严格遵循以下 JSON 格式：
{{
  "title": "标题（≤20字）",
  "body": "正文内容（≤1000字）",
  "tags": ["标签1", "标签2", ...],
  "cover_text": "封面文案建议"
}}

只输出 JSON，不要输出其他内容。"""

def build_user_prompt(source_material: str) -> str:
    return f"请基于以下素材，生成一篇小红书笔记：\n\n{source_material}"
