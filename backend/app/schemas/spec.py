from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


Capability = Literal[
    "rag",
    "document_processing",
    "conversation_memory",
    "guardrails",
    "structured_output",
    "web_research",
    "csv_analysis",
]
MemoryMode = Literal["short_term", "summary", "long_term", "semantic"]
ComponentId = Literal[
    "ChatPanel",
    "DocumentUploader",
    "DocumentList",
    "ConversationHistory",
    "MemoryManager",
    "ModelInfo",
    "AgentConfigPanel",
]


def default_memory_modes() -> list[MemoryMode]:
    return ["short_term"]


def default_component_ids() -> list[ComponentId]:
    return ["ChatPanel"]


class MemorySpec(BaseModel):
    modes: list[MemoryMode] = Field(default_factory=default_memory_modes)
    token_budget: int = Field(default=2000, ge=256, le=16000)
    summarization_enabled: bool = True
    semantic_enabled: bool = False


class ModelPreferences(BaseModel):
    required_capabilities: list[str] = Field(default_factory=list)
    preferred_models: list[str] = Field(default_factory=list)
    fallback_models: list[str] = Field(default_factory=list)


class GuardrailSpec(BaseModel):
    injection_screening: Literal["off", "heuristic", "classifier"] = "heuristic"
    output_checks: list[Literal["redact_secrets", "no_system_prompt_leakage", "citations"]] = Field(
        default_factory=list
    )
    allowed_file_types: list[Literal["pdf", "docx", "txt"]] = Field(default_factory=list)


class UISpec(BaseModel):
    component_ids: list[ComponentId] = Field(default_factory=default_component_ids)
    layout: Literal["single_column", "sidebar", "dashboard"] = "single_column"


class AgentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(default=1, ge=1)
    name: str = Field(min_length=1, max_length=120)
    purpose: str = Field(min_length=1, max_length=4000)
    system_prompt: str = Field(min_length=1, max_length=12000)
    capabilities: list[Capability] = Field(default_factory=list, max_length=8)
    capability_config: dict[str, dict[str, object]] = Field(default_factory=dict)
    memory: MemorySpec = Field(default_factory=MemorySpec)
    model_preferences: ModelPreferences = Field(default_factory=ModelPreferences)
    guardrails: GuardrailSpec = Field(default_factory=GuardrailSpec)
    ui: UISpec = Field(default_factory=UISpec)
    requires_embeddings: bool = False
    access_mode: Literal["private", "public"] = "private"

    @model_validator(mode="after")
    def derive_embedding_requirement(self) -> "AgentSpec":
        embedding_capabilities = {"rag", "document_processing"}
        requires = bool(embedding_capabilities.intersection(self.capabilities)) or (
            self.memory.semantic_enabled
        )
        self.requires_embeddings = requires
        return self
