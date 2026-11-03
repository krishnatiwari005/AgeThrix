from sqlalchemy import delete

from app.database.session import SessionLocal
from app.models.registry import ModelRegistry
from app.schemas.spec import AgentSpec
from app.services.builder import generate_spec
from app.services.groq_client import FakeGroqClient
from app.services.model_registry import seed_registry
from app.services.model_router import RouterError, RouterRequest, select_model


def setup_function() -> None:
    with SessionLocal() as db:
        db.execute(delete(ModelRegistry))
        db.commit()


def test_fake_groq_generates_valid_spec_without_network() -> None:
    client = FakeGroqClient()
    spec = generate_spec(client, "Create a helpful assistant.", "test-model")

    assert isinstance(spec, AgentSpec)
    assert client.calls == 1


def test_router_applies_tpm_ceiling_and_capabilities() -> None:
    with SessionLocal() as db:
        seed_registry(db)
        models = db.query(ModelRegistry).all()
        selected = select_model(
            models,
            RouterRequest(
                preferred_model="openai/gpt-oss-20b",
                required_capabilities=frozenset({"json_schema"}),
                input_tokens=100,
                output_tokens=100,
            ),
        )
        assert selected.model_id == "openai/gpt-oss-20b"
        try:
            select_model(
                models,
                RouterRequest(
                    preferred_model=None,
                    required_capabilities=frozenset({"tool_calling"}),
                    input_tokens=100,
                    output_tokens=100,
                ),
            )
        except RouterError:
            pass
        else:
            raise AssertionError("router must reject unsupported capabilities")
