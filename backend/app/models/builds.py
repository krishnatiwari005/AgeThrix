from uuid import UUID, uuid4

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.auth import TimestampMixin


class AgentConfiguration(TimestampMixin, Base):
    __tablename__ = "agent_configurations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    spec: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    spec_version: Mapped[int] = mapped_column(default=1, nullable=False)
    is_current: Mapped[bool] = mapped_column(default=True, nullable=False)


class AgentDeployment(TimestampMixin, Base):
    __tablename__ = "agent_deployments"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    safe_error: Mapped[str | None] = mapped_column(Text)
    progress: Mapped[int] = mapped_column(default=0, nullable=False)


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
