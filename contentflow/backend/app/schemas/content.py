from pydantic import BaseModel

class GenerateRequest(BaseModel):
    source_material: str
    platform: str = "xiaohongshu"
    brand_tone: str = "casual"

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
