from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


Provider = Literal["groq", "huggingface"]


class CredentialRequest(BaseModel):
    api_key: str = Field(min_length=8, max_length=512)


class CredentialResponse(BaseModel):
    id: UUID
    provider: Provider
    last4: str
    status: str
    last_validated_at: datetime | None
