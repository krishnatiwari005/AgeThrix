from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.auth import current_user
from app.database.session import get_db
from app.models.auth import EncryptedApiCredential, User
from app.schemas.credentials import CredentialRequest, CredentialResponse, Provider
from app.services.encryption import decrypt_secret, encrypt_secret

router = APIRouter(prefix="/api/v1/credentials", tags=["credentials"])


def credential_response(credential: EncryptedApiCredential) -> CredentialResponse:
    return CredentialResponse(
        id=credential.id,
        provider=cast(Provider, credential.provider),
        last4=credential.last4,
        status=credential.status,
        last_validated_at=credential.last_validated_at,
    )


def get_owned_credential(
    provider: Provider, user: User, db: Session
) -> EncryptedApiCredential:
    credential = db.scalar(
        select(EncryptedApiCredential).where(
            EncryptedApiCredential.owner_id == user.id,
            EncryptedApiCredential.provider == provider,
        )
    )
    if credential is None:
        raise HTTPException(status_code=404, detail="Credential not found")
    return credential


@router.get("/{provider}", response_model=CredentialResponse)
def get_credential(
    provider: Provider, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> CredentialResponse:
    return credential_response(get_owned_credential(provider, user, db))


@router.post("/{provider}", response_model=CredentialResponse, status_code=201)
def save_credential(
    provider: Provider,
    payload: CredentialRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> CredentialResponse:
    credential = db.scalar(
        select(EncryptedApiCredential).where(
            EncryptedApiCredential.owner_id == user.id,
            EncryptedApiCredential.provider == provider,
        )
    )
    ciphertext, key_id = encrypt_secret(payload.api_key)
    if credential is None:
        credential = EncryptedApiCredential(
            owner_id=user.id,
            provider=provider,
            ciphertext=ciphertext,
            key_id=key_id,
            last4=payload.api_key[-4:],
            status="unvalidated",
        )
        db.add(credential)
    else:
        credential.ciphertext = ciphertext
        credential.key_id = key_id
        credential.last4 = payload.api_key[-4:]
        credential.status = "unvalidated"
        credential.last_validated_at = None
    db.commit()
    db.refresh(credential)
    return credential_response(credential)


@router.post("/{provider}/validate", response_model=CredentialResponse)
def validate_credential(
    provider: Provider,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> CredentialResponse:
    credential = get_owned_credential(provider, user, db)
    try:
        decrypt_secret(credential.ciphertext, credential.key_id)
    except ValueError:
        credential.status = "invalid"
        db.commit()
        raise HTTPException(status_code=422, detail="Stored credential cannot be decrypted") from None
    credential.status = "stored"
    credential.last_validated_at = None
    db.commit()
    db.refresh(credential)
    return credential_response(credential)


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_credential(
    provider: Provider,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> None:
    credential = get_owned_credential(provider, user, db)
    db.delete(credential)
    db.commit()
