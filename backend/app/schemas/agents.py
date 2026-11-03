from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=4000)
    access_mode: Literal["private", "public"] = "private"


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=4000)
    access_mode: Literal["private", "public"] | None = None


class AgentResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    slug: str
    status: str
    access_mode: str
    model_name: str | None = None
    created_at: datetime
    updated_at: datetime
