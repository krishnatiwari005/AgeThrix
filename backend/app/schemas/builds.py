from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.spec import AgentSpec


class BuildRequest(BaseModel):
    prompt: str = Field(min_length=10, max_length=20000)
    model_preference: str | None = Field(default=None, max_length=120)


BuildStatus = Literal["queued", "awaiting_credentials", "failed", "active"]


class BuildResponse(BaseModel):
    deployment_id: UUID
    status: BuildStatus
    stage: str
    progress: int
    safe_error: str | None


class BuildStatusResponse(BuildResponse):
    updated_at: datetime
    spec: AgentSpec | None = None
