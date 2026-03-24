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
