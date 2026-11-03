from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.auth import TimestampMixin, User


class Agent(TimestampMixin, Base):
    __tablename__ = "agents"
    __table_args__ = (
        Index("ix_agents_owner_id", "owner_id"),
        Index("ix_agents_slug", "slug", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    access_mode: Mapped[str] = mapped_column(String(16), default="private", nullable=False)

    owner: Mapped[User] = relationship(back_populates="agents")
