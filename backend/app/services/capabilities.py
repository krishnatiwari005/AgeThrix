from dataclasses import dataclass
from app.schemas.spec import AgentSpec, Capability


@dataclass(frozen=True)
class CapabilityDefinition:
    capability: Capability
    available: bool
    requires_embeddings: bool
    required_credentials: tuple[str, ...]


CAPABILITY_REGISTRY: dict[Capability, CapabilityDefinition] = {
    "rag": CapabilityDefinition("rag", True, True, ("groq", "huggingface")),
    "document_processing": CapabilityDefinition(
        "document_processing", True, True, ("groq", "huggingface")
    ),
    "conversation_memory": CapabilityDefinition(
        "conversation_memory", True, False, ("groq",)
    ),
    "guardrails": CapabilityDefinition("guardrails", True, False, ("groq",)),
    "structured_output": CapabilityDefinition(
        "structured_output", True, False, ("groq",)
    ),
    "web_research": CapabilityDefinition("web_research", False, False, ("groq",)),
    "csv_analysis": CapabilityDefinition("csv_analysis", False, False, ("groq",)),
}


def resolve_capabilities(spec: AgentSpec) -> list[CapabilityDefinition]:
    definitions = [CAPABILITY_REGISTRY[capability] for capability in spec.capabilities]
    unavailable = [definition.capability for definition in definitions if not definition.available]
    if unavailable:
        names = ", ".join(unavailable)
        raise ValueError(f"Capabilities unavailable in MVP: {names}")
    return definitions
