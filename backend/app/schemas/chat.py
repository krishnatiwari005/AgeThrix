from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal
from uuid import UUID


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    thread_id: UUID | None = None


class ChatResponse(BaseModel):
    message: str


class ConversationMessageResponse(BaseModel):
    id: UUID
    role: Literal["user", "agent"]
    content: str
    created_at: datetime


class ConversationThreadResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
