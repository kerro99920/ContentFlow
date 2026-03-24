from pydantic import BaseModel

class ScheduleCreateRequest(BaseModel):
    name: str
    cron_expression: str
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
