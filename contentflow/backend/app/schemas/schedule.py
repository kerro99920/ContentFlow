from pydantic import BaseModel, Field, field_validator
import re


class ScheduleCreateRequest(BaseModel):
    name: str = Field(max_length=200)
    cron_expression: str
    source_material: str = Field(max_length=5000)
    platforms: list[str] = Field(min_length=1)
    brand_tone: str = "casual"
    brand_profile_id: str | None = None

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v):
        parts = v.strip().split()
        if len(parts) != 5:
            raise ValueError("cron 表达式必须包含 5 个字段（分 时 日 月 周）")
        return v


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
