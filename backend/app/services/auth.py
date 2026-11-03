import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
    User,
)

password_hasher = PasswordHasher()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user_id: UUID) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def decode_access_token(token: str) -> UUID:
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("invalid token type")
    return UUID(str(payload["sub"]))


def issue_refresh_token(db: Session, user: User, family_id: UUID | None = None) -> str:
    raw_token = secrets.token_urlsafe(48)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            family_id=family_id or uuid4(),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
        )
    )
    return raw_token


def revoke_refresh_family(db: Session, family_id: UUID) -> None:
    tokens = db.scalars(
        select(RefreshToken).where(RefreshToken.family_id == family_id)
    ).all()
    for token in tokens:
        token.revoked = True


def consume_refresh_token(db: Session, raw_token: str) -> tuple[User, str]:
    stored = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token))
    )
    generic_error = ValueError("invalid refresh token")
    if stored is None:
        raise generic_error
    now = datetime.now(UTC)
    if stored.revoked or stored.used_at is not None:
        revoke_refresh_family(db, stored.family_id)
        raise generic_error
    if stored.expires_at.replace(tzinfo=UTC) <= now:
        stored.revoked = True
        raise generic_error
    user = db.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise generic_error
    stored.used_at = now
    new_token = issue_refresh_token(db, user, stored.family_id)
    return user, new_token


def create_one_time_token() -> str:
    return secrets.token_urlsafe(32)


def create_password_reset(db: Session, user: User) -> str:
    raw_token = create_one_time_token()
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
    )
    return raw_token


def create_email_verification(db: Session, user: User) -> str:
    raw_token = create_one_time_token()
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
    )
    return raw_token
