# Deployment guide

The Render configuration now defines separate API and worker services, plus a
Vercel SPA. Set values from the backend and frontend `.env.example` files in
the target platform; never commit production secrets.

The worker runs `python -m app.workers.runner`, claims queued jobs with
PostgreSQL row locks, leases them, and retries bounded failures. Configure
`WORKER_LEASE_SECONDS`, `WORKER_MAX_ATTEMPTS`, and `WORKER_POLL_SECONDS`.
Apply the PostgreSQL reference migration before enabling RLS in production and
verify that the API sets the transaction-local tenant context.
