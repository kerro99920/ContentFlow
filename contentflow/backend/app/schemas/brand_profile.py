from pydantic import BaseModel

class BrandProfileCreateRequest(BaseModel):
    name: str
    tone_description: str
    industry_keywords: list[str] | None = None

class BrandProfileResponse(BaseModel):
    id: str
    name: str
    tone_description: str
    system_prompt: str
    industry_keywords: list[str] | None
    created_at: str
