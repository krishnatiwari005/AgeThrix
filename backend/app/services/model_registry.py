from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.registry import ModelRegistry

SEED_MODELS = (
    ("openai/gpt-oss-120b", "OpenAI GPT OSS 120B", 8192, 4096, 30, 1000, 8000, 200000),
    ("openai/gpt-oss-20b", "OpenAI GPT OSS 20B", 8192, 4096, 30, 1000, 8000, 200000),
    ("llama-3.3-70b-versatile", "Llama 3.3 70B Versatile", 8192, 4096, 30, 1000, 8000, 200000),
)


def seed_registry(db: Session) -> None:
    for model_id, display_name, context, completion, rpm, rpd, tpm, tpd in SEED_MODELS:
        if db.scalar(select(ModelRegistry).where(ModelRegistry.model_id == model_id)):
            continue
        db.add(
            ModelRegistry(
                model_id=model_id,
                display_name=display_name,
                kind="chat",
                context_window=context,
                max_completion_tokens=completion,
                default_rpm=rpm,
                default_rpd=rpd,
                default_tpm=tpm,
                default_tpd=tpd,
                capabilities={
                    "tool_calling": False,
                    "json_schema": True,
                    "reasoning": False,
                    "streaming": True,
                },
                restrictions=[],
                verified=False,
                source="seed",
            )
        )
    db.commit()


def sync_registry(db: Session, models: list[dict[str, object]]) -> int:
    updated = 0
    for item in models:
        model_id = item.get("id")
        if not isinstance(model_id, str):
            continue
        record = db.scalar(select(ModelRegistry).where(ModelRegistry.model_id == model_id))
        if record is None:
            record = ModelRegistry(
                model_id=model_id,
                display_name=model_id,
                kind="chat",
                context_window=4096,
                max_completion_tokens=1024,
                default_rpm=30,
                default_rpd=1000,
                default_tpm=6000,
                default_tpd=200000,
                capabilities={"streaming": True},
                restrictions=[],
            )
            db.add(record)
        record.verified = True
        record.verified_at = datetime.now(UTC)
        record.source = "groq_api"
        record.status = "available"
        updated += 1
    db.commit()
    return updated
