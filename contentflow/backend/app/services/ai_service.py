import json
import re
import httpx
from app.config import settings


async def generate_content(system_prompt: str, user_prompt: str) -> dict:
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

    return _parse_json_response(raw_text)


def _parse_json_response(raw_text: str) -> dict:
    """从 AI 响应中提取 JSON，处理 markdown fence 和混合文本"""
    text = raw_text.strip()
    # 去除 markdown code fence
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取第一个 JSON 对象
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"AI 返回了无法解析的内容格式")


async def _call_openai_compatible(
    api_key: str, base_url: str, model: str,
    system_prompt: str, user_prompt: str,
) -> str:
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
                "max_tokens": 4000,
                "temperature": 0.7,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _call_anthropic(system_prompt: str, user_prompt: str) -> str:
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text
