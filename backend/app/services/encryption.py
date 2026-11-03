import base64
import hashlib
import os
from dataclasses import dataclass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def _development_key() -> bytes:
    return hashlib.sha256(b"personal-agent-cloud-development-key").digest()


@dataclass(frozen=True)
class KeyMaterial:
    key_id: str
    key: bytes


def configured_keys() -> list[KeyMaterial]:
    configured = [value.strip() for value in os.getenv("APP_ENCRYPTION_KEYS", "").split(",") if value.strip()]
    if not configured:
        if os.getenv("APP_ENV", "development") == "production":
            raise RuntimeError("APP_ENCRYPTION_KEYS must be configured in production")
        return [KeyMaterial("development", _development_key())]
    keys: list[KeyMaterial] = []
    for encoded in configured:
        try:
            key = base64.urlsafe_b64decode(encoded.encode("ascii"))
        except ValueError as exc:
            raise RuntimeError("APP_ENCRYPTION_KEYS contains invalid base64") from exc
        if len(key) not in (16, 24, 32):
            raise RuntimeError("APP_ENCRYPTION_KEYS values must decode to AES key sizes")
        keys.append(KeyMaterial(hashlib.sha256(key).hexdigest()[:16], key))
    return keys


def encrypt_secret(secret: str) -> tuple[str, str]:
    key_material = configured_keys()[0]
    nonce = os.urandom(12)
    ciphertext = AESGCM(key_material.key).encrypt(nonce, secret.encode("utf-8"), None)
    packed = base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")
    return packed, key_material.key_id


def decrypt_secret(ciphertext: str, key_id: str) -> str:
    packed = base64.urlsafe_b64decode(ciphertext.encode("ascii"))
    nonce, encrypted = packed[:12], packed[12:]
    for key_material in configured_keys():
        if key_material.key_id != key_id:
            continue
        try:
            return AESGCM(key_material.key).decrypt(nonce, encrypted, None).decode("utf-8")
        except (InvalidTag, UnicodeDecodeError) as exc:
            raise ValueError("credential decryption failed") from exc
    raise ValueError("credential encryption key is unavailable")
