from dataclasses import dataclass

from app.models.registry import ModelRegistry


@dataclass(frozen=True)
class RouterRequest:
    preferred_model: str | None
    required_capabilities: frozenset[str]
    input_tokens: int
    output_tokens: int


class RouterError(RuntimeError):
    pass


def select_model(models: list[ModelRegistry], request: RouterRequest) -> ModelRegistry:
    candidates = [
        model
        for model in models
        if model.status == "available"
        and request.required_capabilities.issubset(
            capability for capability, enabled in model.capabilities.items() if enabled
        )
        and request.input_tokens + request.output_tokens <= min(
            model.context_window, int(model.default_tpm * 0.8)
        )
        and request.output_tokens <= model.max_completion_tokens
    ]
    if request.preferred_model:
        candidates.sort(key=lambda model: model.model_id != request.preferred_model)
    if not candidates:
        raise RouterError("No compatible model has sufficient budget")
    return candidates[0]
