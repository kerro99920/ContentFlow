import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column
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
