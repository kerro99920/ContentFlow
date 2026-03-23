import json
import httpx
from app.config import settings


async def generate_content(system_prompt: str, user_prompt: str) -> dict:
    """调用 AI 模型生成内容，返回解析后的 JSON dict。
    优先级：OminiLink(Gemini) → DashScope(Qwen) → Anthropic(Claude)"""
    if settings.ominilink_api_key:
        raw_text = await _call_openai_compatible(
            settings.ominilink_api_key,
            "https://api.ominilink.ai/v1/chat/completions",
            "gemini-2.5-pro",
            system_prompt, user_prompt,
        )
    elif settings.dashscope_api_key:
        raw_text = await _call_openai_compatible(
            settings.dashscope_api_key,
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            "qwen-plus",
            system_prompt, user_prompt,
        )
    elif settings.anthropic_api_key:
        raw_text = await _call_anthropic(system_prompt, user_prompt)
    else:
        raise RuntimeError("未配置任何 AI API Key")

    # 去除可能的 markdown code fence
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(raw_text)


async def _call_openai_compatible(
    api_key: str, base_url: str, model: str,
    system_prompt: str, user_prompt: str,
) -> str:
    """OpenAI 兼容接口（适用于 DashScope、OminiLink 等）"""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 2000,
                "temperature": 0.7,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _call_anthropic(system_prompt: str, user_prompt: str) -> str:
    """Claude API (备选)"""
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text
