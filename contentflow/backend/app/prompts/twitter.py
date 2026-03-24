PLATFORM_RULES = """Twitter/X 推文规范：
- 正文：≤280字符（中文约140字）
- 简洁有力，直击要点
- 善用话题标签 #hashtag（2-3个）
- 可用 emoji 增强表达
- 适当使用线程(Thread)拆分长内容"""

TONE_TEMPLATES = {
    "professional": "专业观点风格：数据驱动，行业洞察，简洁权威，适合商业和技术话题。",
    "casual": "轻松日常风格：像朋友对话，幽默有趣，适合生活分享和互动。",
    "seeding": "种草推荐风格：真实体验，突出亮点，有感染力，适合产品和工具推荐。",
}

def build_system_prompt(tone: str) -> str:
    tone_desc = TONE_TEMPLATES.get(tone, TONE_TEMPLATES["casual"])
    return f"""你是一位专业的 Twitter/X 内容创作专家。
{tone_desc}
{PLATFORM_RULES}

你的输出必须严格遵循以下 JSON 格式：
{{
  "tweet": "主推文内容（≤280字符）",
  "thread": ["线程推文1", "线程推文2"],
  "tags": ["hashtag1", "hashtag2"],
  "engagement_hook": "互动引导语（如提问、投票建议）"
}}

如果内容简短不需要线程，thread 返回空数组 []。
只输出 JSON，不要输出其他内容。"""

def build_user_prompt(source_material: str) -> str:
    return f"请基于以下素材，创作 Twitter/X 推文：\n\n{source_material}"
