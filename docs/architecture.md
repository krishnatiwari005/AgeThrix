# Architecture

Agethrix is a modular monolith. The React frontend communicates
with the FastAPI backend, which will own authentication, tenant isolation,
agent configuration, provider calls, and background jobs.

Phase 1 contains only application assembly and health endpoints. Security
boundaries, persistence, provider integrations, and worker behavior are
implemented in later phases and must not be inferred from this skeleton.

The credential layer stores user-supplied provider keys encrypted with
AES-GCM. Responses expose only the final four characters. In development,
the encryption service uses a deterministic local-only fallback; production
requires `APP_ENCRYPTION_KEYS`. Live provider validation is intentionally
separate from storage validation.

The Groq integration uses the official Python SDK chat-completions API and
JSON-object response mode. The verified contract is recorded from the current
Groq documentation; tests use `FakeGroqClient` and never consume provider
credits. Registry seed values are conservative and remain `verified=false`
until synchronized from a user's live model list.

To rotate keys, configure the new key first in `APP_ENCRYPTION_KEYS`, followed
by the previous key, run `python scripts/rotate_keys.py` from `backend`, verify
the application, and then remove the old key after all rows have been rotated.
