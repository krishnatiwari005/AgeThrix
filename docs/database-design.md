# Database design

PostgreSQL 15+ with pgvector is the planned persistence layer. The Phase 2
authentication schema defines UUID users, Argon2 password hashes, rotating
refresh-token families, password-reset tokens, and email-verification tokens.
Emails are protected by a case-insensitive unique index.

Local tests use SQLite through SQLAlchemy. Tenant-scoped foreign keys and
PostgreSQL row-level security will be added with agent persistence; the
authentication schema deliberately has no tenant data to protect yet.

The PostgreSQL reference migration now enables RLS on credentials, agents,
configurations, deployments, and jobs. Authenticated requests set the
transaction-local `app.user_id`; public agent slug reads are the only
unauthenticated tenant exception.
