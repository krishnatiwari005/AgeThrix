from datetime import UTC, datetime
from secrets import token_urlsafe

import jwt
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db, set_tenant_context
from app.models.auth import EmailVerificationToken, PasswordResetToken, User
from app.schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    TokenRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import (
    consume_refresh_token,
    create_access_token,
    create_email_verification,
    create_password_reset,
    decode_access_token,
    hash_password,
    hash_token,
    issue_refresh_token,
    normalize_email,
    verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
REFRESH_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_token"


def set_auth_cookies(response: Response, refresh_token: str) -> None:
    csrf_token = token_urlsafe(24)
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=settings.refresh_token_days * 86400,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/api/v1/auth",
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf_token,
        max_age=settings.refresh_token_days * 86400,
        httponly=False,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/api/v1/auth",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
    response.delete_cookie(CSRF_COOKIE, path="/api/v1/auth")


def require_csrf(csrf_cookie: str | None, csrf_header: str | None) -> None:
    if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")


def current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    try:
        user_id = decode_access_token(authorization[7:])
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid authentication credentials") from None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    set_tenant_context(db, user.id)
    return user


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    email = normalize_email(str(payload.email))
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="Unable to create account")
    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    issue_refresh = issue_refresh_token(db, user)
    create_email_verification(db, user)
    db.commit()
    set_auth_cookies(response, issue_refresh)
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == normalize_email(str(payload.email))))
    if user is None or not verify_password(payload.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if settings.require_email_verification and not user.email_verified:
        raise HTTPException(status_code=403, detail="Email verification required")
    refresh_token = issue_refresh_token(db, user)
    db.commit()
    set_auth_cookies(response, refresh_token)
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    csrf_token: str | None = Cookie(default=None),
    x_csrf_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> TokenResponse:
    require_csrf(csrf_token, x_csrf_token)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    try:
        user, new_refresh_token = consume_refresh_token(db, refresh_token)
    except ValueError:
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid refresh token") from None
    db.commit()
    set_auth_cookies(response, new_refresh_token)
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    csrf_token: str | None = Cookie(default=None),
    x_csrf_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Response:
    require_csrf(csrf_token, x_csrf_token)
    if refresh_token:
        from app.models.auth import RefreshToken

        stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token)))
        if stored:
            stored.revoked = True
            db.commit()
    clear_auth_cookies(response)
    return response


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(current_user)) -> User:
    return user


@router.post("/forgot-password", status_code=202)
def forgot_password(payload: PasswordResetRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    user = db.scalar(select(User).where(User.email == normalize_email(str(payload.email))))
    if user:
        create_password_reset(db, user)
        db.commit()
    return {"status": "accepted"}


@router.post("/reset-password", status_code=204)
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)) -> Response:
    stored = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(payload.token))
    )
    if stored is None or stored.used_at is not None or stored.expires_at.replace(tzinfo=UTC) <= datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user = db.get(User, stored.user_id)
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user.password_hash = hash_password(payload.password)
    stored.used_at = datetime.now(UTC)
    db.commit()
    return Response(status_code=204)


@router.post("/verify-email", status_code=204)
def verify_email(payload: TokenRequest, db: Session = Depends(get_db)) -> Response:
    stored = db.scalar(
        select(EmailVerificationToken).where(EmailVerificationToken.token_hash == hash_token(payload.token))
    )
    if stored is None or stored.used_at is not None or stored.expires_at.replace(tzinfo=UTC) <= datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    user = db.get(User, stored.user_id)
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    user.email_verified = True
    stored.used_at = datetime.now(UTC)
    db.commit()
    return Response(status_code=204)
