from datetime import datetime

from pydantic import BaseModel


class ModelResponse(BaseModel):
    model_id: str
    display_name: str
    kind: str
    context_window: int
    max_completion_tokens: int
    capabilities: dict[str, bool]
    status: str
    verified: bool
    verified_at: datetime | None
