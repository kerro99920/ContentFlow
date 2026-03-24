from typing import Literal
from pydantic import BaseModel, Field

PLATFORM_TYPE = Literal["xiaohongshu", "douyin", "wechat", "blog"]
TONE_TYPE = Literal["professional", "casual", "seeding"]


class GenerateRequest(BaseModel):
    source_material: str = Field(max_length=5000)
    platform: PLATFORM_TYPE = "xiaohongshu"
    brand_tone: TONE_TYPE = "casual"


class GenerateResponse(BaseModel):
    task_id: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    content_id: str | None = None
    error_message: str | None = None


class ContentResponse(BaseModel):
    id: str
    platform: str
    title: str | None
    body: str | None
    tags: list | None
    metadata: dict | None
    brand_tone: str | None
    status: str
    created_at: str


class ContentListResponse(BaseModel):
    items: list[ContentResponse]
    total: int
    page: int
    page_size: int


class BatchGenerateRequest(BaseModel):
    source_material: str = Field(max_length=5000)
    platforms: list[PLATFORM_TYPE] = Field(min_length=1)
    brand_tone: TONE_TYPE = "casual"
    brand_profile_id: str | None = None


class BatchGenerateResponse(BaseModel):
    task_ids: dict[str, str]


class ContentUpdateRequest(BaseModel):
    title: str | None = None
    body: str | None = None
    tags: list[str] | None = None
    status: str | None = None
