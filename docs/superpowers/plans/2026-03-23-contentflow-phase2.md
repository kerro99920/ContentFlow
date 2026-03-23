# ContentFlow Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand ContentFlow from single-platform (Xiaohongshu) to multi-platform content generation (Douyin/WeChat/Blog), add workflow automation with scheduled tasks and email notifications, custom brand templates, and content management enhancements (edit/status/calendar/copy).

**Architecture:** Extend existing FastAPI backend with new prompt templates per platform, platform registry pattern in generation_service, APScheduler for cron tasks, SMTP for email. Extend Next.js frontend with new dashboard pages and enhanced components.

**Tech Stack:** Existing (FastAPI, SQLAlchemy, Next.js, shadcn/ui) + APScheduler, aiosmtplib

**Spec:** `docs/superpowers/specs/2026-03-23-contentflow-phase2-design.md`

---

## File Structure (New/Modified)

```
contentflow/backend/
├── app/
│   ├── config.py                          # MODIFY: add SMTP settings
│   ├── main.py                            # MODIFY: register new routers, start scheduler
│   ├── models/
│   │   ├── __init__.py                    # MODIFY: export new models
│   │   ├── content.py                     # MODIFY: add brand_profile_id FK
│   │   ├── brand_profile.py               # CREATE
│   │   └── schedule.py                    # CREATE
│   ├── prompts/
│   │   ├── xiaohongshu.py                 # MODIFY: extract shared pattern
│   │   ├── douyin.py                      # CREATE
│   │   ├── wechat.py                      # CREATE
│   │   ├── blog.py                        # CREATE
│   │   └── registry.py                    # CREATE: platform dispatch
│   ├── schemas/
│   │   ├── content.py                     # MODIFY: add batch + update schemas
│   │   ├── brand_profile.py               # CREATE
│   │   └── schedule.py                    # CREATE
│   ├── routers/
│   │   ├── content.py                     # MODIFY: batch generate, PUT, calendar
│   │   ├── brand_profile.py               # CREATE
│   │   └── schedule.py                    # CREATE
│   └── services/
│       ├── generation_service.py          # MODIFY: platform registry, brand profile
│       ├── brand_service.py               # CREATE
│       ├── schedule_service.py            # CREATE
│       └── email_service.py               # CREATE
├── tests/
│   ├── test_prompts.py                    # CREATE
│   ├── test_brand.py                      # CREATE
│   ├── test_schedule.py                   # CREATE
│   ├── test_content_v2.py                 # CREATE
│   └── test_email.py                      # CREATE

contentflow/frontend/src/
├── app/(dashboard)/
│   ├── brands/page.tsx                    # CREATE
│   ├── schedules/page.tsx                 # CREATE
│   └── calendar/page.tsx                  # CREATE
├── components/
│   ├── dashboard/sidebar.tsx              # MODIFY: add nav items
│   ├── content/
│   │   ├── generate-form.tsx              # MODIFY: multi-platform + brand select
│   │   ├── content-card.tsx               # MODIFY: edit/copy/status buttons
│   │   ├── platform-tabs.tsx              # CREATE
│   │   ├── edit-modal.tsx                 # CREATE
│   │   └── copy-button.tsx                # CREATE
│   ├── brand/
│   │   ├── brand-form.tsx                 # CREATE
│   │   └── brand-list.tsx                 # CREATE
│   ├── schedule/
│   │   ├── schedule-form.tsx              # CREATE
│   │   └── schedule-list.tsx              # CREATE
│   └── calendar/
│       └── month-view.tsx                 # CREATE
└── lib/types.ts                           # MODIFY: add new types
```

---

## Task 1: New Platform Prompt Templates

**Files:**
- Create: `contentflow/backend/app/prompts/douyin.py`
- Create: `contentflow/backend/app/prompts/wechat.py`
- Create: `contentflow/backend/app/prompts/blog.py`
- Create: `contentflow/backend/app/prompts/registry.py`
- Create: `contentflow/backend/tests/test_prompts.py`
- Modify: `contentflow/backend/app/services/generation_service.py`

- [ ] **Step 1: Create douyin prompt template**

```python
# contentflow/backend/app/prompts/douyin.py
PLATFORM_RULES = """抖音短视频脚本规范：
- 总时长：15-60秒
- 前3秒必须有强钩子（冲突/悬念/价值）
- 竖版 9:16 拍摄
- 必须包含分镜描述、台词、BGM建议"""

TONE_TEMPLATES = {
    "professional": "专业权威风格：数据驱动，行业视角，适合知识科普类短视频。",
    "casual": "轻松日常风格：像朋友分享一样，口语化表达，适合生活vlog。",
    "seeding": "种草安利风格：真实体验感，突出产品使用场景和效果，适合好物推荐。",
}

def build_system_prompt(tone: str) -> str:
    tone_desc = TONE_TEMPLATES.get(tone, TONE_TEMPLATES["casual"])
    return f"""你是一位专业的抖音短视频脚本创作专家。
{tone_desc}
{PLATFORM_RULES}

你的输出必须严格遵循以下 JSON 格式：
{{
  "hook": "前3秒钩子台词",
  "script_sections": [
    {{"time": "0-3s", "scene": "场景描述", "dialogue": "台词", "camera": "镜头运动"}},
    {{"time": "3-15s", "scene": "场景描述", "dialogue": "台词", "camera": "镜头运动"}}
  ],
  "bgm_suggestion": "推荐BGM风格或具体歌曲",
  "subtitle_text": "字幕文案（完整台词）",
  "total_duration": "预计总时长（如30s）"
}}

只输出 JSON，不要输出其他内容。"""

def build_user_prompt(source_material: str) -> str:
    return f"请基于以下素材，创作一个抖音短视频脚本：\n\n{source_material}"
```

- [ ] **Step 2: Create wechat prompt template**

```python
# contentflow/backend/app/prompts/wechat.py
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
```

- [ ] **Step 3: Create blog prompt template**

```python
# contentflow/backend/app/prompts/blog.py
PLATFORM_RULES = """博客SEO文章规范：
- 标题：含关键词，吸引搜索点击
- 正文：800-2000字，含H2/H3标题结构
- Meta Description：≤160字
- 关键词：3-5个，含长尾关键词"""

TONE_TEMPLATES = {
    "professional": "专业技术风格：准确严谨，适合技术博客和行业分析。",
    "casual": "轻松科普风格：通俗易懂，适合入门教程和经验分享。",
    "seeding": "产品评测风格：客观评价，突出优缺点，适合产品对比和推荐。",
}

def build_system_prompt(tone: str) -> str:
    tone_desc = TONE_TEMPLATES.get(tone, TONE_TEMPLATES["casual"])
    return f"""你是一位专业的SEO博客内容创作专家。
{tone_desc}
{PLATFORM_RULES}

你的输出必须严格遵循以下 JSON 格式：
{{
  "title": "文章标题（含SEO关键词）",
  "body": "正文内容（800-2000字，Markdown格式，含H2/H3）",
  "meta_description": "Meta描述（≤160字）",
  "keywords": ["关键词1", "关键词2", "关键词3"],
  "headings": ["H2标题1", "H2标题2"]
}}

只输出 JSON，不要输出其他内容。"""

def build_user_prompt(source_material: str) -> str:
    return f"请基于以下素材，撰写一篇SEO优化的博客文章：\n\n{source_material}"
```

- [ ] **Step 4: Create platform registry**

```python
# contentflow/backend/app/prompts/registry.py
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
    """返回 (build_system_prompt, build_user_prompt) 或 raise"""
    if platform not in PLATFORM_PROMPTS:
        raise ValueError(f"不支持的平台: {platform}")
    return PLATFORM_PROMPTS[platform]

def get_validator(platform: str):
    return VALIDATORS.get(platform, lambda _: True)
```

- [ ] **Step 5: Refactor generation_service to use registry**

Replace the hardcoded imports in `contentflow/backend/app/services/generation_service.py`:

```python
# contentflow/backend/app/services/generation_service.py
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.content import Content, GenerationTask
from app.services.ai_service import generate_content
from app.services.usage_service import increment_usage
from app.prompts.registry import get_prompt_builders, get_validator


async def run_generation(
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    source_material: str,
    platform: str,
    brand_tone: str,
    custom_system_prompt: str | None = None,
) -> None:
    """后台任务：执行 AI 生成并保存结果。使用独立 DB session。"""
    from app.database import async_session
    async with async_session() as db:
        await _do_generation(db, task_id, user_id, source_material, platform, brand_tone, custom_system_prompt)


async def _do_generation(
    db: AsyncSession,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    source_material: str,
    platform: str,
    brand_tone: str,
    custom_system_prompt: str | None = None,
) -> None:
    task = await db.get(GenerationTask, task_id)
    task.status = "running"
    await db.commit()

    try:
        build_system, build_user = get_prompt_builders(platform)
        if custom_system_prompt:
            system_prompt = custom_system_prompt
        else:
            system_prompt = build_system(brand_tone)
        user_prompt = build_user(source_material)
        validator = get_validator(platform)

        result = None
        for attempt in range(3):
            result = await generate_content(system_prompt, user_prompt)
            if validator(result):
                break
        else:
            task.status = "failed"
            task.error_message = "内容校验未通过，请重试"
            await db.commit()
            return

        content = Content(
            user_id=user_id,
            source_material=source_material,
            platform=platform,
            title=result.get("title"),
            body=result.get("body") or result.get("subtitle_text"),
            tags=result.get("tags") or result.get("keywords"),
            metadata_=result,
            brand_tone=brand_tone,
            status="draft",
        )
        db.add(content)
        await db.flush()

        task.status = "completed"
        task.content_id = content.id
        await increment_usage(db, user_id)
        await db.commit()

    except Exception as e:
        task.status = "failed"
        task.error_message = str(e)
        await db.commit()
```

- [ ] **Step 6: Write prompt tests**

```python
# contentflow/backend/tests/test_prompts.py
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
```

- [ ] **Step 7: Run tests**

Run: `cd contentflow/backend && uv run pytest tests/test_prompts.py -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add contentflow/backend/app/prompts/ contentflow/backend/app/services/generation_service.py contentflow/backend/tests/test_prompts.py
git commit -m "feat: add douyin/wechat/blog prompt templates with platform registry"
```

---

## Task 2: Batch Generation API

**Files:**
- Modify: `contentflow/backend/app/schemas/content.py`
- Modify: `contentflow/backend/app/routers/content.py`
- Create: `contentflow/backend/tests/test_content_v2.py`

- [ ] **Step 1: Add batch schemas**

Add to `contentflow/backend/app/schemas/content.py`:

```python
class BatchGenerateRequest(BaseModel):
    source_material: str
    platforms: list[str]  # ["xiaohongshu", "douyin", "wechat", "blog"]
    brand_tone: str = "casual"
    brand_profile_id: str | None = None

class BatchGenerateResponse(BaseModel):
    task_ids: dict[str, str]  # {platform: task_id}

class ContentUpdateRequest(BaseModel):
    title: str | None = None
    body: str | None = None
    tags: list[str] | None = None
    status: str | None = None

class CalendarItem(BaseModel):
    date: str
    items: list[ContentResponse]

class CalendarResponse(BaseModel):
    month: str
    days: list[CalendarItem]
```

- [ ] **Step 2: Add batch generate endpoint**

Add to `contentflow/backend/app/routers/content.py`:

```python
@router.post("/generate-batch", response_model=BatchGenerateResponse, status_code=202)
async def generate_batch(
    req: BatchGenerateRequest,
    bg: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.services.usage_service import get_usage
    usage = await get_usage(db, user.id)
    remaining = usage["quota"] - usage["generation_count"]
    if remaining < len(req.platforms):
        raise HTTPException(
            status_code=403,
            detail={"code": "QUOTA_EXCEEDED", "message": f"配额不足：剩余{remaining}次，需要{len(req.platforms)}次"},
        )

    # 获取自定义品牌模板的 system_prompt
    custom_prompt = None
    if req.brand_profile_id:
        from app.models.brand_profile import BrandProfile
        bp = await db.get(BrandProfile, uuid.UUID(req.brand_profile_id))
        if bp and bp.user_id == user.id:
            custom_prompt = bp.system_prompt

    task_ids = {}
    for platform in req.platforms:
        task = GenerationTask(
            user_id=user.id,
            source_material=req.source_material,
            platform=platform,
            brand_tone=req.brand_tone,
        )
        db.add(task)
        await db.flush()
        bg.add_task(run_generation, task.id, user.id, req.source_material, platform, req.brand_tone, custom_prompt)
        task_ids[platform] = str(task.id)

    await db.commit()
    return BatchGenerateResponse(task_ids=task_ids)
```

- [ ] **Step 3: Add PUT and calendar endpoints**

Add to `contentflow/backend/app/routers/content.py`:

```python
@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: str,
    req: ContentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await db.get(Content, uuid.UUID(content_id))
    if not content or content.user_id != user.id:
        raise HTTPException(status_code=404, detail="Content not found")
    if req.title is not None:
        content.title = req.title
    if req.body is not None:
        content.body = req.body
    if req.tags is not None:
        content.tags = req.tags
    if req.status is not None:
        content.status = req.status
    await db.commit()
    await db.refresh(content)
    return ContentResponse(
        id=str(content.id), platform=content.platform, title=content.title,
        body=content.body, tags=content.tags, metadata=content.metadata_,
        brand_tone=content.brand_tone, status=content.status,
        created_at=content.created_at.isoformat(),
    )

@router.get("/calendar")
async def get_calendar(
    month: str = Query(..., regex=r"^\d{4}-\d{2}$"),
    platform: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from sqlalchemy import extract
    year, mon = map(int, month.split("-"))
    query = select(Content).where(
        Content.user_id == user.id,
        extract("year", Content.created_at) == year,
        extract("month", Content.created_at) == mon,
    )
    if platform:
        query = query.where(Content.platform == platform)
    if status:
        query = query.where(Content.status == status)
    query = query.order_by(Content.created_at)
    result = await db.execute(query)

    from collections import defaultdict
    days = defaultdict(list)
    for c in result.scalars():
        day = c.created_at.strftime("%Y-%m-%d")
        days[day].append(ContentResponse(
            id=str(c.id), platform=c.platform, title=c.title, body=c.body,
            tags=c.tags, metadata=c.metadata_, brand_tone=c.brand_tone,
            status=c.status, created_at=c.created_at.isoformat(),
        ))
    return {"month": month, "days": [{"date": k, "items": v} for k, v in sorted(days.items())]}
```

- [ ] **Step 4: Write tests**

```python
# contentflow/backend/tests/test_content_v2.py
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_batch_generate(authed_client: AsyncClient):
    with patch("app.routers.content.run_generation", new_callable=AsyncMock):
        resp = await authed_client.post("/api/content/generate-batch", json={
            "source_material": "test material",
            "platforms": ["xiaohongshu", "douyin"],
            "brand_tone": "casual",
        })
    assert resp.status_code == 202
    data = resp.json()
    assert "xiaohongshu" in data["task_ids"]
    assert "douyin" in data["task_ids"]

@pytest.mark.asyncio
async def test_batch_exceeds_quota(authed_client: AsyncClient, db_session, test_user):
    from app.services.usage_service import increment_usage
    for _ in range(9):
        await increment_usage(db_session, test_user.id)
    resp = await authed_client.post("/api/content/generate-batch", json={
        "source_material": "test",
        "platforms": ["xiaohongshu", "douyin"],
        "brand_tone": "casual",
    })
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_update_content(authed_client: AsyncClient, db_session, test_user):
    from app.models.content import Content
    c = Content(user_id=test_user.id, source_material="s", platform="xiaohongshu", title="old", status="draft")
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    resp = await authed_client.put(f"/api/content/{c.id}", json={"title": "new", "status": "approved"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "new"
    assert resp.json()["status"] == "approved"

@pytest.mark.asyncio
async def test_calendar(authed_client: AsyncClient):
    resp = await authed_client.get("/api/content/calendar?month=2026-03")
    assert resp.status_code == 200
    assert "month" in resp.json()
    assert "days" in resp.json()
```

- [ ] **Step 5: Import new schemas in content router**

Update imports in `content.py` to include `BatchGenerateRequest`, `BatchGenerateResponse`, `ContentUpdateRequest`.

- [ ] **Step 6: Run all tests**

Run: `cd contentflow/backend && uv run pytest tests/ -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add contentflow/backend/
git commit -m "feat: add batch generation, content edit, and calendar API"
```

---

## Task 3: Brand Profile Model + API

**Files:**
- Create: `contentflow/backend/app/models/brand_profile.py`
- Create: `contentflow/backend/app/schemas/brand_profile.py`
- Create: `contentflow/backend/app/services/brand_service.py`
- Create: `contentflow/backend/app/routers/brand_profile.py`
- Create: `contentflow/backend/tests/test_brand.py`
- Modify: `contentflow/backend/app/models/__init__.py`
- Modify: `contentflow/backend/app/main.py`

- [ ] **Step 1: Create BrandProfile model**

```python
# contentflow/backend/app/models/brand_profile.py
import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class BrandProfile(Base):
    __tablename__ = "brand_profiles"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    tone_description: Mapped[str] = mapped_column(Text)
    system_prompt: Mapped[str] = mapped_column(Text)
    industry_keywords: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 2: Create schemas**

```python
# contentflow/backend/app/schemas/brand_profile.py
from pydantic import BaseModel

class BrandProfileCreateRequest(BaseModel):
    name: str
    tone_description: str
    industry_keywords: list[str] | None = None

class BrandProfileUpdateRequest(BaseModel):
    name: str | None = None
    tone_description: str | None = None
    industry_keywords: list[str] | None = None

class BrandProfileResponse(BaseModel):
    id: str
    name: str
    tone_description: str
    system_prompt: str
    industry_keywords: list[str] | None
    created_at: str
```

- [ ] **Step 3: Create brand service (AI generates system_prompt)**

```python
# contentflow/backend/app/services/brand_service.py
from app.services.ai_service import generate_content
import json

BRAND_PROMPT_GENERATOR = """你是一个AI提示词工程专家。用户描述了一个品牌调性，请生成一个系统提示词(system prompt)，
用于指导AI以该品牌调性生成社交媒体内容。

输出JSON格式：
{"system_prompt": "生成的系统提示词"}

只输出JSON。"""

async def generate_brand_system_prompt(tone_description: str, keywords: list[str] | None = None) -> str:
    """调用 AI 根据用户描述生成品牌 system_prompt"""
    user_msg = f"品牌调性描述：{tone_description}"
    if keywords:
        user_msg += f"\n行业关键词：{', '.join(keywords)}"
    try:
        result = await generate_content(BRAND_PROMPT_GENERATOR, user_msg)
        return result.get("system_prompt", tone_description)
    except Exception:
        # 降级：直接用用户描述作为 prompt
        return f"请以以下风格创作内容：{tone_description}"
```

- [ ] **Step 4: Create brand profile router**

```python
# contentflow/backend/app/routers/brand_profile.py
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.brand_profile import BrandProfile
from app.schemas.brand_profile import (
    BrandProfileCreateRequest, BrandProfileUpdateRequest, BrandProfileResponse,
)
from app.services.brand_service import generate_brand_system_prompt

router = APIRouter(prefix="/api/brand-profiles", tags=["brand-profiles"])

@router.post("", response_model=BrandProfileResponse, status_code=201)
async def create_brand_profile(
    req: BrandProfileCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    system_prompt = await generate_brand_system_prompt(req.tone_description, req.industry_keywords)
    bp = BrandProfile(
        user_id=user.id,
        name=req.name,
        tone_description=req.tone_description,
        system_prompt=system_prompt,
        industry_keywords=req.industry_keywords,
    )
    db.add(bp)
    await db.commit()
    await db.refresh(bp)
    return BrandProfileResponse(
        id=str(bp.id), name=bp.name, tone_description=bp.tone_description,
        system_prompt=bp.system_prompt, industry_keywords=bp.industry_keywords,
        created_at=bp.created_at.isoformat(),
    )

@router.get("", response_model=list[BrandProfileResponse])
async def list_brand_profiles(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(BrandProfile).where(BrandProfile.user_id == user.id))
    return [
        BrandProfileResponse(
            id=str(bp.id), name=bp.name, tone_description=bp.tone_description,
            system_prompt=bp.system_prompt, industry_keywords=bp.industry_keywords,
            created_at=bp.created_at.isoformat(),
        )
        for bp in result.scalars()
    ]

@router.delete("/{profile_id}", status_code=204)
async def delete_brand_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    bp = await db.get(BrandProfile, uuid.UUID(profile_id))
    if not bp or bp.user_id != user.id:
        raise HTTPException(status_code=404)
    await db.delete(bp)
    await db.commit()
```

- [ ] **Step 5: Update models/__init__.py and main.py**

`models/__init__.py`: Add `from app.models.brand_profile import BrandProfile` and to `__all__`.

`main.py`: Add `from app.routers import brand_profile` and `app.include_router(brand_profile.router)`.

- [ ] **Step 6: Write tests**

```python
# contentflow/backend/tests/test_brand.py
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

@pytest.mark.asyncio
@patch("app.services.brand_service.generate_content", new_callable=AsyncMock)
async def test_create_brand_profile(mock_ai, authed_client: AsyncClient):
    mock_ai.return_value = {"system_prompt": "mocked prompt"}
    resp = await authed_client.post("/api/brand-profiles", json={
        "name": "测试品牌",
        "tone_description": "活泼有趣的美妆博主",
        "industry_keywords": ["美妆", "护肤"],
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "测试品牌"
    assert resp.json()["system_prompt"] == "mocked prompt"

@pytest.mark.asyncio
async def test_list_brand_profiles(authed_client: AsyncClient):
    resp = await authed_client.get("/api/brand-profiles")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
```

- [ ] **Step 7: Re-init database (add new table)**

Run: `cd contentflow/backend && uv run python init_db.py`

- [ ] **Step 8: Run all tests**

Run: `cd contentflow/backend && uv run pytest tests/ -v`
Expected: All PASS

- [ ] **Step 9: Commit**

```bash
git add contentflow/backend/
git commit -m "feat: add brand profile CRUD with AI-generated system prompts"
```

---

## Task 4: Scheduled Tasks Model + Service

**Files:**
- Create: `contentflow/backend/app/models/schedule.py`
- Create: `contentflow/backend/app/schemas/schedule.py`
- Create: `contentflow/backend/app/services/schedule_service.py`
- Create: `contentflow/backend/app/services/email_service.py`
- Create: `contentflow/backend/app/routers/schedule.py`
- Create: `contentflow/backend/tests/test_schedule.py`
- Modify: `contentflow/backend/app/config.py`
- Modify: `contentflow/backend/app/models/__init__.py`
- Modify: `contentflow/backend/app/main.py`
- Modify: `contentflow/backend/pyproject.toml`

- [ ] **Step 1: Add dependencies**

Run: `cd contentflow/backend && uv add apscheduler aiosmtplib`

- [ ] **Step 2: Add SMTP config**

Add to `contentflow/backend/app/config.py`:

```python
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
```

- [ ] **Step 3: Create Schedule models**

```python
# contentflow/backend/app/models/schedule.py
import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    cron_expression: Mapped[str] = mapped_column(String(50))
    source_material: Mapped[str] = mapped_column(Text)
    platforms: Mapped[list] = mapped_column(JSON)
    brand_tone: Mapped[str] = mapped_column(String(50), default="casual")
    brand_profile_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("brand_profiles.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class ScheduledTaskRun(Base):
    __tablename__ = "scheduled_task_runs"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    scheduled_task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scheduled_tasks.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_content_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
```

- [ ] **Step 4: Create schedule schemas**

```python
# contentflow/backend/app/schemas/schedule.py
from pydantic import BaseModel

class ScheduleCreateRequest(BaseModel):
    name: str
    cron_expression: str  # "0 9 * * *"
    source_material: str
    platforms: list[str]
    brand_tone: str = "casual"
    brand_profile_id: str | None = None

class ScheduleUpdateRequest(BaseModel):
    name: str | None = None
    cron_expression: str | None = None
    source_material: str | None = None
    platforms: list[str] | None = None
    brand_tone: str | None = None
    is_active: bool | None = None

class ScheduleResponse(BaseModel):
    id: str
    name: str
    cron_expression: str
    source_material: str
    platforms: list[str]
    brand_tone: str
    is_active: bool
    last_run_at: str | None
    created_at: str

class ScheduleRunResponse(BaseModel):
    id: str
    status: str
    started_at: str
    finished_at: str | None
    error_message: str | None
    generated_content_ids: list[str] | None
```

- [ ] **Step 5: Create email service**

```python
# contentflow/backend/app/services/email_service.py
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


async def send_email(to: str, subject: str, html_body: str) -> bool:
    """发送邮件。SMTP 未配置时静默跳过。"""
    if not settings.smtp_host or not settings.smtp_user:
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.smtp_from or settings.smtp_user
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            use_tls=True,
        )
        return True
    except Exception:
        return False


def build_content_email(contents: list[dict], task_name: str) -> str:
    """构建内容通知邮件 HTML"""
    items_html = ""
    for c in contents:
        items_html += f"""
        <div style="border:1px solid #eee;padding:12px;margin:8px 0;border-radius:8px;">
            <strong>[{c.get('platform','')}]</strong> {c.get('title','无标题')}<br>
            <small style="color:#666;">{(c.get('body',''))[:100]}...</small>
        </div>"""
    return f"""
    <h2>ContentFlow - {task_name} 已完成</h2>
    <p>以下内容已自动生成，请登录查看完整内容：</p>
    {items_html}
    <p style="color:#999;font-size:12px;">此邮件由 ContentFlow 自动发送</p>
    """
```

- [ ] **Step 6: Create schedule service (APScheduler)**

```python
# contentflow/backend/app/services/schedule_service.py
import uuid
from datetime import datetime, timezone
from apscheduler import AsyncScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schedule import ScheduledTask, ScheduledTaskRun
from app.models.content import Content, GenerationTask
from app.models.brand_profile import BrandProfile
from app.services.generation_service import _do_generation
from app.services.email_service import send_email, build_content_email
from app.models.user import User

scheduler = AsyncScheduler()


async def init_scheduler():
    """应用启动时加载所有活跃定时任务"""
    from app.database import async_session
    async with async_session() as db:
        result = await db.execute(select(ScheduledTask).where(ScheduledTask.is_active == True))
        for task in result.scalars():
            _add_job(task)
    await scheduler.start_in_background()


def _parse_cron(expr: str) -> CronTrigger:
    """解析 cron 表达式 'minute hour day month day_of_week'"""
    parts = expr.split()
    if len(parts) == 5:
        return CronTrigger(minute=parts[0], hour=parts[1], day=parts[2], month=parts[3], day_of_week=parts[4])
    return CronTrigger(hour=9)  # 默认每天9点


def _add_job(task: ScheduledTask):
    """向 scheduler 添加任务"""
    scheduler.add_schedule(
        execute_scheduled_task,
        _parse_cron(task.cron_expression),
        id=str(task.id),
        args=[str(task.id)],
        conflict_policy="replace",
    )


def remove_job(task_id: str):
    try:
        scheduler.remove_schedule(task_id)
    except Exception:
        pass


async def execute_scheduled_task(task_id: str):
    """执行定时任务：生成内容 + 发邮件"""
    from app.database import async_session
    async with async_session() as db:
        task = await db.get(ScheduledTask, uuid.UUID(task_id))
        if not task or not task.is_active:
            return

        run = ScheduledTaskRun(scheduled_task_id=task.id)
        db.add(run)
        await db.flush()

        # 获取自定义品牌 prompt
        custom_prompt = None
        if task.brand_profile_id:
            bp = await db.get(BrandProfile, task.brand_profile_id)
            if bp:
                custom_prompt = bp.system_prompt

        content_ids = []
        errors = []
        for platform in task.platforms:
            try:
                gen_task = GenerationTask(
                    user_id=task.user_id,
                    source_material=task.source_material,
                    platform=platform,
                    brand_tone=task.brand_tone,
                )
                db.add(gen_task)
                await db.flush()
                await _do_generation(db, gen_task.id, task.user_id, task.source_material, platform, task.brand_tone, custom_prompt)
                await db.refresh(gen_task)
                if gen_task.content_id:
                    content_ids.append(str(gen_task.content_id))
            except Exception as e:
                errors.append(f"{platform}: {str(e)}")

        # 更新运行记录
        run.status = "completed" if not errors else "failed"
        run.finished_at = datetime.now(timezone.utc)
        run.generated_content_ids = content_ids
        run.error_message = "; ".join(errors) if errors else None
        task.last_run_at = datetime.now(timezone.utc)
        await db.commit()

        # 发送邮件通知
        if content_ids:
            user = await db.get(User, task.user_id)
            contents = []
            for cid in content_ids:
                c = await db.get(Content, uuid.UUID(cid))
                if c:
                    contents.append({"platform": c.platform, "title": c.title, "body": c.body})
            html = build_content_email(contents, task.name)
            await send_email(user.email, f"ContentFlow: {task.name} 已完成", html)
```

- [ ] **Step 7: Create schedule router**

```python
# contentflow/backend/app/routers/schedule.py
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.schedule import ScheduledTask
from app.schemas.schedule import (
    ScheduleCreateRequest, ScheduleUpdateRequest, ScheduleResponse,
)
from app.services.schedule_service import _add_job, remove_job, execute_scheduled_task

router = APIRouter(prefix="/api/schedules", tags=["schedules"])

def _to_response(t: ScheduledTask) -> ScheduleResponse:
    return ScheduleResponse(
        id=str(t.id), name=t.name, cron_expression=t.cron_expression,
        source_material=t.source_material, platforms=t.platforms,
        brand_tone=t.brand_tone, is_active=t.is_active,
        last_run_at=t.last_run_at.isoformat() if t.last_run_at else None,
        created_at=t.created_at.isoformat(),
    )

@router.post("", response_model=ScheduleResponse, status_code=201)
async def create_schedule(
    req: ScheduleCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = ScheduledTask(
        user_id=user.id, name=req.name, cron_expression=req.cron_expression,
        source_material=req.source_material, platforms=req.platforms,
        brand_tone=req.brand_tone, brand_profile_id=uuid.UUID(req.brand_profile_id) if req.brand_profile_id else None,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    _add_job(task)
    return _to_response(task)

@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(ScheduledTask).where(ScheduledTask.user_id == user.id))
    return [_to_response(t) for t in result.scalars()]

@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: str,
    req: ScheduleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = await db.get(ScheduledTask, uuid.UUID(schedule_id))
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404)
    for field, value in req.model_dump(exclude_none=True).items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    remove_job(str(task.id))
    if task.is_active:
        _add_job(task)
    return _to_response(task)

@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = await db.get(ScheduledTask, uuid.UUID(schedule_id))
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404)
    remove_job(str(task.id))
    await db.delete(task)
    await db.commit()

@router.post("/{schedule_id}/run", status_code=202)
async def run_schedule_now(
    schedule_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from fastapi import BackgroundTasks
    task = await db.get(ScheduledTask, uuid.UUID(schedule_id))
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404)
    # 直接异步执行
    import asyncio
    asyncio.create_task(execute_scheduled_task(str(task.id)))
    return {"message": "任务已触发"}
```

- [ ] **Step 8: Update models/__init__.py and main.py**

`models/__init__.py`: Add ScheduledTask, ScheduledTaskRun imports.

`main.py`: Add schedule router. Add lifespan for scheduler:

```python
from contextlib import asynccontextmanager
from app.services.schedule_service import init_scheduler

@asynccontextmanager
async def lifespan(app):
    await init_scheduler()
    yield

app = FastAPI(title="ContentFlow API", version="0.2.0", lifespan=lifespan)
```

- [ ] **Step 9: Write tests**

```python
# contentflow/backend/tests/test_schedule.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_schedule(authed_client: AsyncClient):
    resp = await authed_client.post("/api/schedules", json={
        "name": "每日生成",
        "cron_expression": "0 9 * * *",
        "source_material": "每日咖啡推荐",
        "platforms": ["xiaohongshu"],
        "brand_tone": "casual",
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "每日生成"
    assert resp.json()["is_active"] is True

@pytest.mark.asyncio
async def test_list_schedules(authed_client: AsyncClient):
    resp = await authed_client.get("/api/schedules")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

@pytest.mark.asyncio
async def test_delete_schedule(authed_client: AsyncClient):
    create = await authed_client.post("/api/schedules", json={
        "name": "temp", "cron_expression": "0 9 * * *",
        "source_material": "x", "platforms": ["xiaohongshu"],
    })
    sid = create.json()["id"]
    resp = await authed_client.delete(f"/api/schedules/{sid}")
    assert resp.status_code == 204
```

- [ ] **Step 10: Re-init database and run all tests**

```bash
cd contentflow/backend && uv run python init_db.py && uv run pytest tests/ -v
```

- [ ] **Step 11: Commit**

```bash
git add contentflow/backend/
git commit -m "feat: add scheduled tasks with APScheduler and email notifications"
```

---

## Task 5: Frontend — Multi-Platform Generation + Tabs

**Files:**
- Modify: `contentflow/frontend/src/lib/types.ts`
- Modify: `contentflow/frontend/src/components/content/generate-form.tsx`
- Create: `contentflow/frontend/src/components/content/platform-tabs.tsx`
- Modify: `contentflow/frontend/src/app/(dashboard)/generate/page.tsx`

- [ ] **Step 1: Update types.ts**

Add new types to `contentflow/frontend/src/lib/types.ts`:

```typescript
export interface BatchGenerateResponse {
  task_ids: Record<string, string>;
}

export interface BrandProfile {
  id: string;
  name: string;
  tone_description: string;
  system_prompt: string;
  industry_keywords: string[] | null;
  created_at: string;
}

export interface ScheduledTask {
  id: string;
  name: string;
  cron_expression: string;
  source_material: string;
  platforms: string[];
  brand_tone: string;
  is_active: boolean;
  last_run_at: string | null;
  created_at: string;
}

export interface CalendarDay {
  date: string;
  items: ContentItem[];
}

export interface CalendarResponse {
  month: string;
  days: CalendarDay[];
}

export const PLATFORMS = [
  { value: "xiaohongshu", label: "小红书" },
  { value: "douyin", label: "抖音" },
  { value: "wechat", label: "公众号" },
  { value: "blog", label: "博客" },
] as const;
```

- [ ] **Step 2: Update generate-form for multi-platform**

Rewrite `generate-form.tsx` to support multi-platform checkbox selection and brand profile dropdown. Use `POST /api/content/generate-batch`. Poll each task_id independently. Call `onGenerated` with array of results.

Key changes:
- Platform selection: checkbox group (select multiple)
- Brand profile: fetch from `/api/brand-profiles`, add to select dropdown
- Submit calls `/api/content/generate-batch`
- Poll all task_ids in parallel
- Return all generated contents

- [ ] **Step 3: Create platform-tabs component**

```tsx
// contentflow/frontend/src/components/content/platform-tabs.tsx
"use client";
import { ContentCard } from "./content-card";
import { Button } from "@/components/ui/button";
import type { ContentItem } from "@/lib/types";
import { useState } from "react";

interface Props {
  contents: ContentItem[];
}

const PLATFORM_LABELS: Record<string, string> = {
  xiaohongshu: "小红书",
  douyin: "抖音",
  wechat: "公众号",
  blog: "博客",
};

export function PlatformTabs({ contents }: Props) {
  const platforms = [...new Set(contents.map((c) => c.platform))];
  const [active, setActive] = useState(platforms[0] || "");

  return (
    <div>
      <div className="mb-4 flex gap-2">
        {platforms.map((p) => (
          <Button
            key={p}
            variant={active === p ? "default" : "outline"}
            size="sm"
            onClick={() => setActive(p)}
          >
            {PLATFORM_LABELS[p] || p}
          </Button>
        ))}
      </div>
      {contents
        .filter((c) => c.platform === active)
        .map((c) => (
          <ContentCard key={c.id} content={c} />
        ))}
    </div>
  );
}
```

- [ ] **Step 4: Update generate page**

Update `src/app/(dashboard)/generate/page.tsx` to use `PlatformTabs` for displaying multi-platform results.

- [ ] **Step 5: Verify build**

Run: `cd contentflow/frontend && npm run build`

- [ ] **Step 6: Commit**

```bash
git add contentflow/frontend/
git commit -m "feat: multi-platform content generation with tab display"
```

---

## Task 6: Frontend — Content Management (Edit/Copy/Status)

**Files:**
- Create: `contentflow/frontend/src/components/content/edit-modal.tsx`
- Create: `contentflow/frontend/src/components/content/copy-button.tsx`
- Modify: `contentflow/frontend/src/components/content/content-card.tsx`

- [ ] **Step 1: Create copy-button component**

```tsx
// contentflow/frontend/src/components/content/copy-button.tsx
"use client";
import { Button } from "@/components/ui/button";
import type { ContentItem } from "@/lib/types";
import { useState } from "react";

function formatForCopy(content: ContentItem): string {
  if (content.platform === "xiaohongshu") {
    const tags = content.tags?.map((t) => `#${t}`).join(" ") || "";
    return `${content.title}\n\n${content.body}\n\n${tags}`;
  }
  if (content.platform === "douyin") {
    const meta = content.metadata as Record<string, unknown> | null;
    return meta?.subtitle_text as string || content.body || "";
  }
  return `${content.title}\n\n${content.body}`;
}

export function CopyButton({ content }: { content: ContentItem }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(formatForCopy(content));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Button variant="outline" size="sm" onClick={handleCopy}>
      {copied ? "已复制" : "复制"}
    </Button>
  );
}
```

- [ ] **Step 2: Create edit-modal component**

```tsx
// contentflow/frontend/src/components/content/edit-modal.tsx
"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { ContentItem } from "@/lib/types";

interface Props {
  content: ContentItem;
  onSaved: (updated: ContentItem) => void;
  onCancel: () => void;
}

export function EditModal({ content, onSaved, onCancel }: Props) {
  const [title, setTitle] = useState(content.title || "");
  const [body, setBody] = useState(content.body || "");
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await api.fetch<ContentItem>(`/api/content/${content.id}`, {
        method: "PUT",
        body: JSON.stringify({ title, body }),
      });
      onSaved(updated);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="mt-4">
      <CardHeader><CardTitle>编辑内容</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label>标题</Label>
          <Input value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>
        <div>
          <Label>正文</Label>
          <Textarea value={body} onChange={(e) => setBody(e.target.value)} rows={10} />
        </div>
        <div className="flex gap-2">
          <Button onClick={handleSave} disabled={saving}>{saving ? "保存中..." : "保存"}</Button>
          <Button variant="outline" onClick={onCancel}>取消</Button>
        </div>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 3: Update content-card with edit/copy/status buttons**

Add CopyButton, edit button, and status badge to content-card.tsx. Add status change buttons (draft→approved→published).

- [ ] **Step 4: Verify build**

Run: `cd contentflow/frontend && npm run build`

- [ ] **Step 5: Commit**

```bash
git add contentflow/frontend/
git commit -m "feat: content edit modal, copy button, status management"
```

---

## Task 7: Frontend — Brand Profiles Page

**Files:**
- Create: `contentflow/frontend/src/components/brand/brand-form.tsx`
- Create: `contentflow/frontend/src/components/brand/brand-list.tsx`
- Create: `contentflow/frontend/src/app/(dashboard)/brands/page.tsx`
- Modify: `contentflow/frontend/src/components/dashboard/sidebar.tsx`

- [ ] **Step 1: Create brand-form and brand-list components**

Brand form: name + tone_description textarea + industry_keywords input. Calls `POST /api/brand-profiles`.
Brand list: fetches from `GET /api/brand-profiles`, displays cards with delete button.

- [ ] **Step 2: Create brands page**

```tsx
// contentflow/frontend/src/app/(dashboard)/brands/page.tsx
"use client";
import { useState } from "react";
import { BrandForm } from "@/components/brand/brand-form";
import { BrandList } from "@/components/brand/brand-list";

export default function BrandsPage() {
  const [refresh, setRefresh] = useState(0);
  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-6 text-2xl font-bold">品牌模板</h1>
      <BrandForm onCreated={() => setRefresh((r) => r + 1)} />
      <div className="mt-8">
        <BrandList key={refresh} />
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Update sidebar navigation**

Add to `navItems` in sidebar.tsx:
```typescript
{ href: "/brands", label: "品牌模板" },
{ href: "/schedules", label: "自动任务" },
{ href: "/calendar", label: "日历" },
```

- [ ] **Step 4: Verify build and commit**

```bash
cd contentflow/frontend && npm run build
cd D:/agency-agents && git add contentflow/frontend/ && git commit -m "feat: brand profiles management page"
```

---

## Task 8: Frontend — Schedules Page

**Files:**
- Create: `contentflow/frontend/src/components/schedule/schedule-form.tsx`
- Create: `contentflow/frontend/src/components/schedule/schedule-list.tsx`
- Create: `contentflow/frontend/src/app/(dashboard)/schedules/page.tsx`

- [ ] **Step 1: Create schedule-form**

Form with: name, source_material textarea, platform checkboxes, brand_tone select, cron preset select (每天9点/每天21点/工作日9点/自定义). Calls `POST /api/schedules`.

Cron presets:
```typescript
const CRON_PRESETS = [
  { label: "每天 9:00", value: "0 9 * * *" },
  { label: "每天 21:00", value: "0 21 * * *" },
  { label: "工作日 9:00", value: "0 9 * * 1-5" },
  { label: "每周一 9:00", value: "0 9 * * 1" },
];
```

- [ ] **Step 2: Create schedule-list**

Fetches from `GET /api/schedules`. Each item shows: name, platforms, cron, active toggle, last run time, run now button, delete button.

- [ ] **Step 3: Create schedules page**

Similar pattern to brands page.

- [ ] **Step 4: Verify build and commit**

```bash
cd contentflow/frontend && npm run build
cd D:/agency-agents && git add contentflow/frontend/ && git commit -m "feat: scheduled tasks management page"
```

---

## Task 9: Frontend — Calendar Page

**Files:**
- Create: `contentflow/frontend/src/components/calendar/month-view.tsx`
- Create: `contentflow/frontend/src/app/(dashboard)/calendar/page.tsx`

- [ ] **Step 1: Create month-view component**

Fetches from `GET /api/content/calendar?month=YYYY-MM`. Renders a 7-column grid (Mon-Sun). Each day cell shows content count and platform badges. Click on a day to expand and show content cards.

- [ ] **Step 2: Create calendar page**

Month navigation (prev/next), platform filter dropdown, status filter dropdown.

- [ ] **Step 3: Verify build and commit**

```bash
cd contentflow/frontend && npm run build
cd D:/agency-agents && git add contentflow/frontend/ && git commit -m "feat: content calendar view"
```

---

## Task 10: Integration Test + Deploy

- [ ] **Step 1: Re-init database on server**

In WindTerm:
```bash
cd /opt/contentflow/backend && uv run python init_db.py
```

- [ ] **Step 2: Run all backend tests**

```bash
cd contentflow/backend && uv run pytest tests/ -v
```
Expected: All PASS

- [ ] **Step 3: Build frontend**

```bash
cd contentflow/frontend && npm run build
```
Expected: Build success

- [ ] **Step 4: Push to GitHub**

```bash
git push contentflow feat/contentflow-phase1
```

- [ ] **Step 5: Update server**

In WindTerm:
```bash
cd /opt/contentflow && git pull origin feat/contentflow-phase1
cd backend && uv sync && uv run python init_db.py && systemctl restart contentflow
```

- [ ] **Step 6: E2E verification**

1. 注册/登录
2. 创建品牌模板
3. 一次素材生成 4 个平台内容（批量）
4. Tab 切换查看各平台结果
5. 编辑内容，修改状态
6. 一键复制内容
7. 创建定时任务
8. 手动触发定时任务
9. 查看日历视图

- [ ] **Step 7: Final commit**

```bash
git add -A && git commit -m "feat: ContentFlow Phase 2 complete"
```
