PLATFORM_RULES = """哔哩哔哩（B站）内容规范：
- 标题：≤80字，吸引点击，可用【】标注类型
- 简介：≤250字，含关键词，引导三连
- 标签：5-10个，含热门标签和垂直标签
- 分区适配：科技、生活、知识、美食等
- 弹幕互动：预设弹幕引导语"""

TONE_TEMPLATES = {
    "professional": "专业UP主风格：硬核测评，数据说话，逻辑清晰，适合科技和知识区。",
    "casual": "日常UP主风格：轻松有趣，像朋友聊天，适合生活区和vlog。",
    "seeding": "种草UP主风格：真实体验分享，突出使用场景，适合好物推荐和开箱。",
}

def build_system_prompt(tone: str) -> str:
    tone_desc = TONE_TEMPLATES.get(tone, TONE_TEMPLATES["casual"])
    return f"""你是一位专业的B站内容创作专家。
{tone_desc}
{PLATFORM_RULES}

你的输出必须严格遵循以下 JSON 格式：
{{
  "title": "视频标题（≤80字）",
  "description": "视频简介（≤250字，含关键词和三连引导）",
  "tags": ["标签1", "标签2", "标签3"],
  "partition": "推荐分区（如：科技、生活、知识）",
  "danmaku_hooks": ["弹幕引导语1", "弹幕引导语2"],
  "cover_text": "封面文字建议"
}}

只输出 JSON，不要输出其他内容。"""

def build_user_prompt(source_material: str) -> str:
    return f"请基于以下素材，创作一条B站视频的标题、简介和标签：\n\n{source_material}"
