"""Re-encrypt all stored credentials with the first configured key.

Set APP_ENCRYPTION_KEYS to "new_key,old_key" before running this script.
"""

from app.database.session import SessionLocal
from app.models.auth import EncryptedApiCredential
from app.services.encryption import decrypt_secret, encrypt_secret


def main() -> None:
    updated = 0
    with SessionLocal() as db:
        credentials = db.query(EncryptedApiCredential).all()
        for credential in credentials:
            secret = decrypt_secret(credential.ciphertext, credential.key_id)
            ciphertext, key_id = encrypt_secret(secret)
            credential.ciphertext = ciphertext
            credential.key_id = key_id
            updated += 1
        db.commit()
    print(f"Rotated {updated} credential(s).")


if __name__ == "__main__":
    main()
