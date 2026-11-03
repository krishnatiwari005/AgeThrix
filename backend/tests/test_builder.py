from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database.session import SessionLocal
from app.models.agents import Agent
from app.models.auth import (
    EmailVerificationToken,
    EncryptedApiCredential,
    PasswordResetToken,
    RefreshToken,
    User,
)
from app.models.builds import AgentConfiguration, AgentDeployment, Job
from app.schemas.spec import AgentSpec
from app.services.capabilities import resolve_capabilities
from main import app


client = TestClient(app)


def setup_function() -> None:
    with SessionLocal() as db:
        db.execute(delete(AgentConfiguration))
        db.execute(delete(AgentDeployment))
        db.execute(delete(Job))
        db.execute(delete(Agent))
        db.execute(delete(EncryptedApiCredential))
        db.execute(delete(EmailVerificationToken))
        db.execute(delete(PasswordResetToken))
        db.execute(delete(RefreshToken))
        db.execute(delete(User))
        db.commit()


def test_spec_derives_embeddings_and_rejects_unknown_fields() -> None:
    spec = AgentSpec(
        name="Docs helper",
        purpose="Answer questions from uploaded documents",
        system_prompt="Use the supplied sources.",
        capabilities=["rag"],
    )
    assert spec.requires_embeddings is True
    assert resolve_capabilities(spec)[0].required_credentials == ("groq", "huggingface")

    try:
        AgentSpec(
            name="Invalid",
            purpose="Test",
            system_prompt="Test",
            unknown_field=True,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("unknown AgentSpec fields must be rejected")


def test_build_pauses_without_groq_credential_and_persists_status() -> None:
    registration = client.post(
        "/api/v1/auth/register",
        json={"email": "builder@example.com", "password": "correct horse battery"},
    )
    headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}
    agent = client.post(
        "/api/v1/agents", json={"name": "Builder"}, headers=headers
    ).json()

    build = client.post(
        f"/api/v1/agents/{agent['id']}/build",
        json={"prompt": "Create a helpful research assistant."},
        headers=headers,
    )
    assert build.status_code == 202
    assert build.json()["status"] == "awaiting_credentials"

    status = client.get(
        f"/api/v1/agents/{agent['id']}/build-status", headers=headers
    )
    assert status.status_code == 200
    assert status.json()["safe_error"] is None
    assert status.json()["stage"] == "configuring_models"


def test_unavailable_capability_is_rejected() -> None:
    spec = AgentSpec(
        name="Research",
        purpose="Search the web",
        system_prompt="Use sources.",
        capabilities=["web_research"],
    )
    try:
        resolve_capabilities(spec)
    except ValueError as error:
        assert "web_research" in str(error)
    else:
        raise AssertionError("unavailable capabilities must be rejected")
