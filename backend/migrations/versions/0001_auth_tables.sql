-- Phase 2 reference migration for PostgreSQL 15+.
-- Alembic Python revisions will replace this SQL before production deployment.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name varchar(120) NOT NULL DEFAULT '',
    email varchar(320) NOT NULL,
    password_hash varchar(255) NOT NULL,
    email_verified boolean NOT NULL DEFAULT false,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email_lower ON users (lower(email));

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash varchar(64) NOT NULL UNIQUE,
    family_id uuid NOT NULL,
    expires_at timestamptz NOT NULL,
    revoked boolean NOT NULL DEFAULT false,
    used_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_family_id ON refresh_tokens (family_id);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash varchar(64) NOT NULL UNIQUE,
    expires_at timestamptz NOT NULL,
    used_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash varchar(64) NOT NULL UNIQUE,
    expires_at timestamptz NOT NULL,
    used_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS encrypted_api_credentials (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider varchar(32) NOT NULL,
    ciphertext varchar(4096) NOT NULL,
    key_id varchar(32) NOT NULL,
    last4 varchar(4) NOT NULL,
    status varchar(32) NOT NULL DEFAULT 'unknown',
    last_validated_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_credentials_owner_provider UNIQUE (owner_id, provider)
);

CREATE TABLE IF NOT EXISTS agents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name varchar(120) NOT NULL,
    description text,
    slug varchar(160) NOT NULL UNIQUE,
    status varchar(32) NOT NULL DEFAULT 'draft',
    access_mode varchar(16) NOT NULL DEFAULT 'private',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_agents_owner_id ON agents (owner_id);

CREATE TABLE IF NOT EXISTS agent_configurations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id uuid NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    spec jsonb NOT NULL,
    spec_version integer NOT NULL DEFAULT 1,
    is_current boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_agent_configurations_current
    ON agent_configurations (agent_id, is_current);

CREATE TABLE IF NOT EXISTS agent_deployments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id uuid NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status varchar(32) NOT NULL,
    stage varchar(64) NOT NULL,
    safe_error text,
    progress integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id uuid NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    type varchar(64) NOT NULL,
    payload jsonb NOT NULL,
    status varchar(32) NOT NULL DEFAULT 'queued',
    attempts integer NOT NULL DEFAULT 0,
    locked_until timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id uuid NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    thread_id uuid,
    role varchar(16) NOT NULL CHECK (role IN ('user', 'agent')),
    content text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_conversation_messages_owner_agent_created
    ON conversation_messages (owner_id, agent_id, created_at);

CREATE TABLE IF NOT EXISTS conversation_threads (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id uuid NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    client_key varchar(100),
    title varchar(160) NOT NULL DEFAULT 'New conversation',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE conversation_messages
    ADD CONSTRAINT fk_conversation_messages_thread
    FOREIGN KEY (thread_id) REFERENCES conversation_threads(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS ix_conversation_threads_owner_agent_updated
    ON conversation_threads (owner_id, agent_id, updated_at);
CREATE UNIQUE INDEX IF NOT EXISTS uq_conversation_threads_client_key
    ON conversation_threads (owner_id, agent_id, client_key)
    WHERE client_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS model_registry (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id varchar(160) NOT NULL UNIQUE,
    display_name varchar(200) NOT NULL,
    kind varchar(32) NOT NULL,
    context_window integer NOT NULL,
    max_completion_tokens integer NOT NULL,
    default_rpm integer NOT NULL,
    default_rpd integer NOT NULL,
    default_tpm integer NOT NULL,
    default_tpd integer NOT NULL,
    capabilities jsonb NOT NULL,
    restrictions jsonb NOT NULL,
    status varchar(32) NOT NULL DEFAULT 'available',
    verified boolean NOT NULL DEFAULT false,
    verified_at timestamptz,
    source varchar(32) NOT NULL DEFAULT 'seed',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- Tenant isolation. Authenticated requests must set app.user_id with SET LOCAL
-- (the application does this after validating the access token).
ALTER TABLE encrypted_api_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_deployments ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_threads ENABLE ROW LEVEL SECURITY;

CREATE POLICY credentials_owner_policy ON encrypted_api_credentials
    USING (owner_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
    WITH CHECK (owner_id = NULLIF(current_setting('app.user_id', true), '')::uuid);

CREATE POLICY agents_owner_or_public_read_policy ON agents
    FOR SELECT USING (
        access_mode = 'public'
        OR owner_id = NULLIF(current_setting('app.user_id', true), '')::uuid
    );
CREATE POLICY agents_owner_write_policy ON agents
    FOR INSERT WITH CHECK (
        owner_id = NULLIF(current_setting('app.user_id', true), '')::uuid
    );
CREATE POLICY agents_owner_update_policy ON agents
    FOR UPDATE USING (
        owner_id = NULLIF(current_setting('app.user_id', true), '')::uuid
    ) WITH CHECK (
        owner_id = NULLIF(current_setting('app.user_id', true), '')::uuid
    );
CREATE POLICY agents_owner_delete_policy ON agents
    FOR DELETE USING (
        owner_id = NULLIF(current_setting('app.user_id', true), '')::uuid
    );

CREATE POLICY configurations_owner_policy ON agent_configurations
    USING (owner_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
    WITH CHECK (owner_id = NULLIF(current_setting('app.user_id', true), '')::uuid);
CREATE POLICY deployments_owner_policy ON agent_deployments
    USING (owner_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
    WITH CHECK (owner_id = NULLIF(current_setting('app.user_id', true), '')::uuid);
CREATE POLICY jobs_owner_policy ON jobs
    USING (owner_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
    WITH CHECK (owner_id = NULLIF(current_setting('app.user_id', true), '')::uuid);

CREATE POLICY conversation_messages_owner_policy ON conversation_messages
    USING (owner_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
    WITH CHECK (owner_id = NULLIF(current_setting('app.user_id', true), '')::uuid);

CREATE POLICY conversation_threads_owner_policy ON conversation_threads
    USING (owner_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
    WITH CHECK (owner_id = NULLIF(current_setting('app.user_id', true), '')::uuid);
