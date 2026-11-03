from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.auth import TimestampMixin


class ModelRegistry(TimestampMixin, Base):
    __tablename__ = "model_registry"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    model_id: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    context_window: Mapped[int] = mapped_column(Integer, default=4096, nullable=False)
    max_completion_tokens: Mapped[int] = mapped_column(Integer, default=1024, nullable=False)
    default_rpm: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    default_rpd: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    default_tpm: Mapped[int] = mapped_column(Integer, default=6000, nullable=False)
    default_tpd: Mapped[int] = mapped_column(Integer, default=200000, nullable=False)
    capabilities: Mapped[dict[str, bool]] = mapped_column(JSON, nullable=False)
    restrictions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="available", nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(32), default="seed", nullable=False)
