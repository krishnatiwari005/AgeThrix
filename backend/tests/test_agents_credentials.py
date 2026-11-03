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
from app.services.encryption import decrypt_secret
from main import app


client = TestClient(app)


def setup_function() -> None:
    with SessionLocal() as db:
        db.execute(delete(Agent))
        db.execute(delete(EncryptedApiCredential))
        db.execute(delete(EmailVerificationToken))
        db.execute(delete(PasswordResetToken))
        db.execute(delete(RefreshToken))
        db.execute(delete(User))
        db.commit()


def auth_headers(email: str) -> dict[str, str]:
    result = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct horse battery"},
    )
    return {"Authorization": f"Bearer {result.json()['access_token']}"}


def test_credentials_are_encrypted_and_masked() -> None:
    headers = auth_headers("credentials@example.com")
    saved = client.post(
        "/api/v1/credentials/groq",
        json={"api_key": "gsk_super_secret_key_1234"},
        headers=headers,
    )

    assert saved.status_code == 201
    assert saved.json()["last4"] == "1234"
    assert "gsk_super_secret_key_1234" not in saved.text

    with SessionLocal() as db:
        credential = db.query(EncryptedApiCredential).one()
        assert credential.ciphertext != "gsk_super_secret_key_1234"
        assert decrypt_secret(credential.ciphertext, credential.key_id) == "gsk_super_secret_key_1234"


def test_agent_crud_is_owner_scoped() -> None:
    owner_headers = auth_headers("owner@example.com")
    other_headers = auth_headers("other@example.com")
    created = client.post(
        "/api/v1/agents",
        json={"name": "Research Assistant", "description": "Private helper"},
        headers=owner_headers,
    )
    assert created.status_code == 201
    agent_id = created.json()["id"]
    assert created.json()["slug"].startswith("research-assistant-")

    hidden = client.get(f"/api/v1/agents/{agent_id}", headers=other_headers)
    assert hidden.status_code == 404
    listed = client.get("/api/v1/agents", headers=owner_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_public_agent_can_be_loaded_by_slug() -> None:
    headers = auth_headers("public@example.com")
    created = client.post(
        "/api/v1/agents",
        json={"name": "Public Helper", "access_mode": "public"},
        headers=headers,
    ).json()

    public = client.get(f"/api/v1/agents/by-slug/{created['slug']}")
    assert public.status_code == 200
    assert public.json()["slug"] == created["slug"]


def test_credential_validation_and_revoke() -> None:
    headers = auth_headers("revoke@example.com")
    client.post(
        "/api/v1/credentials/huggingface",
        json={"api_key": "hf_super_secret_key_1234"},
        headers=headers,
    )
    validated = client.post(
        "/api/v1/credentials/huggingface/validate", headers=headers
    )
    assert validated.status_code == 200
    assert validated.json()["status"] == "stored"
    revoked = client.delete("/api/v1/credentials/huggingface", headers=headers)
    assert revoked.status_code == 204
    assert client.get("/api/v1/credentials/huggingface", headers=headers).status_code == 404
