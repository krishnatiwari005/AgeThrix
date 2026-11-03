from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database.session import SessionLocal
from app.models.auth import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
    User,
)
from main import app


client = TestClient(app)


def setup_function() -> None:
    with SessionLocal() as db:
        db.execute(delete(EmailVerificationToken))
        db.execute(delete(PasswordResetToken))
        db.execute(delete(RefreshToken))
        db.execute(delete(User))
        db.commit()


def test_register_and_me() -> None:
    registration = client.post(
        "/api/v1/auth/register",
        json={"email": "User@Example.com", "password": "correct horse battery"},
    )
    assert registration.status_code == 201
    access_token = registration.json()["access_token"]

    profile = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert profile.status_code == 200
    assert profile.json()["email"] == "user@example.com"


def test_refresh_rotates_and_reuse_revokes_family() -> None:
    registration = client.post(
        "/api/v1/auth/register",
        json={"email": "rotate@example.com", "password": "correct horse battery"},
    )
    assert registration.status_code == 201
    refresh_cookie = client.cookies.get("refresh_token")
    csrf_cookie = client.cookies.get("csrf_token")
    assert refresh_cookie and csrf_cookie

    rotated = client.post(
        "/api/v1/auth/refresh", headers={"X-CSRF-Token": csrf_cookie}
    )
    assert rotated.status_code == 200
    rotated_cookie = client.cookies.get("refresh_token")
    rotated_csrf = client.cookies.get("csrf_token")
    assert rotated_cookie and rotated_cookie != refresh_cookie
    assert rotated_csrf

    client.cookies.set("refresh_token", refresh_cookie, path="/api/v1/auth")
    reused = client.post(
        "/api/v1/auth/refresh",
        headers={"X-CSRF-Token": rotated_csrf},
    )
    assert reused.status_code == 401

    client.cookies.set("refresh_token", rotated_cookie, path="/api/v1/auth")
    after_reuse = client.post(
        "/api/v1/auth/refresh",
        headers={"X-CSRF-Token": rotated_csrf},
    )
    assert after_reuse.status_code == 401


def test_login_rejects_wrong_password() -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "correct horse battery"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "wrong password"},
    )
    assert login.status_code == 401
    assert login.json() == {"detail": "Invalid email or password"}


def test_email_uniqueness_is_case_insensitive() -> None:
    first = client.post(
        "/api/v1/auth/register",
        json={"email": "duplicate@example.com", "password": "correct horse battery"},
    )
    second = client.post(
        "/api/v1/auth/register",
        json={"email": "DUPLICATE@example.com", "password": "correct horse battery"},
    )

    assert first.status_code == 201
    assert second.status_code == 409
