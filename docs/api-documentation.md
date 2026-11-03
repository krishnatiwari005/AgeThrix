# API documentation

Phase 1 exposes:

- `GET /health` for a cheap liveness check.
- `GET /health/ready` for the readiness contract.

Authentication, agent, credential, build, memory, document, model, and chat
endpoints are added in their respective phases.

The current implemented agent endpoints include:

- `POST|GET /api/v1/agents`
- `GET|PATCH|DELETE /api/v1/agents/{id}`
- `POST /api/v1/agents/{id}/build`
- `GET /api/v1/agents/{id}/build-status`
- `POST|GET|DELETE /api/v1/credentials/{groq|huggingface}`
- `GET /api/v1/models`
- `POST /api/v1/agents/{id}/build/resume`

Build requests are persisted and return `awaiting_credentials` when a stored
Groq credential is missing. A provider-backed builder is not claimed active
until the Groq integration phase.

After credentials are added, the resume endpoint performs one bounded Groq
builder attempt. Production deployment still requires moving this attempt into
the PostgreSQL-backed worker loop.

The Groq adapter and fake client are implemented in
`backend/app/services/groq_client.py`. The real adapter is used only when a
worker supplies a decrypted, owner-scoped credential; tests use the fake
adapter and make no network calls.
