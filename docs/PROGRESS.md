# Progress

Status values: `not started`, `in progress`, `implemented`, `verified`.

## Phase 1 - Skeleton

- [x] `implemented` Repository layout and configuration files
- [x] `implemented` FastAPI application assembly
- [x] `implemented` Liveness and readiness endpoints
- [x] `implemented` React/Vite TypeScript entry point
- [x] `implemented` Environment examples and deployment skeleton
- [x] `implemented` CI workflow
- [x] `verified` Backend tests, lint, type-check, and frontend build/lint
- [x] `implemented` Frontend smoke test

## Later phases

- [x] `implemented` Database foundation and authentication endpoints
- [x] `verified` Registration, login, protected profile, CSRF-protected refresh,
  rotating refresh tokens, reuse detection, logout, reset and verification
  token persistence, and case-insensitive email uniqueness
- [ ] `in progress` PostgreSQL RLS policies and bypass isolation tests
- [x] `implemented` Encrypted BYOK credential storage and owner-scoped agent CRUD
- [x] `verified` AES-GCM masking, credential ownership, agent ownership, slug
  uniqueness, update/delete flows, and per-user agent limits
- [x] `implemented` AgentSpec validation, capability registry, persisted build
  jobs, deployment status, and awaiting-credentials pause
- [x] `verified` Closed AgentSpec fields, derived embedding requirements,
  unavailable-capability rejection, and build status persistence
- [x] `verified` Credential and agent management vertical slice
- [x] `verified` Agent specification and builder lifecycle persistence
- [x] `implemented` Live Groq builder execution boundary, authenticated resume
  endpoint, bounded provider failure handling, and frontend resume action
- [x] `implemented` Durable worker loop, PostgreSQL-compatible row-lock claim,
  leases, bounded retries, and Render worker service
- [x] `verified` Worker claim/completion/retry behavior against PostgreSQL
- [ ] `in progress` Live provider validation in deployment environments
- [x] `implemented` Groq SDK adapter, fake client, model registry seed/sync,
  token-budget router, and bounded builder execution
- [x] `verified` Groq JSON-mode adapter contract and router tests without network
- [ ] `not started` Groq integration and model router
- [x] `verified` Groq integration and model router foundation
- [ ] `not started` Memory, embeddings, and guardrails
- [ ] `not started` Runtime and RAG
- [x] `implemented` Frontend routes, auth context, API services, dashboard,
  agent creation, build progress, credentials, settings, dynamic workspace,
  component registry, responsive states, and error handling
- [x] `verified` Frontend TypeScript lint, production build, and Vitest
- [ ] `in progress` Chat SSE, document upload/RAG, memory controls, and runtime
  actions pending their backend APIs
- [ ] `not started` Integration hardening
- [ ] `not started` Production deployment

## Assumptions

- Phase 1 uses a dependency-light health endpoint; database readiness checks are
  intentionally deferred until the database layer is introduced.
- No provider API details are implemented in Phase 1, so no external API
  verification was required.
- Phase 2 uses SQLite for local tests. PostgreSQL-specific RLS policies require
  tenant tables and are intentionally completed alongside agent persistence
  before Phase 2 can be marked fully verified.
- Credential validation currently verifies decryptability only and reports
  `stored`; live Groq/Hugging Face validation belongs to the provider integration
  phase and is not represented as successful here.
- The current resume endpoint executes one build attempt synchronously behind an
  authenticated API call. A PostgreSQL `FOR UPDATE SKIP LOCKED` worker with
  leases and retry policy remains before production readiness.
- The worker implementation now provides the `FOR UPDATE SKIP LOCKED` claim and
  retry policy; applying the reference RLS migration and live provider
  validation remain deployment verification tasks.
