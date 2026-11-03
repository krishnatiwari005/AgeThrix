# Agethrix

> **From Intent to Intelligence.**

Agethrix is an AI agent-building platform that transforms natural-language
ideas into personalized AI workspaces. Users describe what they need,
configure their agent, provide their own model credentials, and use the
resulting agent through a dedicated workspace.

The platform follows three principles:

**BUILD · PERSONALIZE · DEPLOY**

## Product ecosystem

### Agethrix Studio

The agent creation environment. Users describe an agent in natural language,
and the builder converts that intent into a validated agent specification.

### Agethrix Cloud

The hosting and deployment environment. Completed agents become available
through unique workspace URLs.

### Agethrix Memory

The isolated context layer for agents. It stores conversations and provides
agent-specific memory foundations without mixing data between agents.

### Agethrix Hub

The central dashboard where users manage their agents, credentials, builds and
workspaces.

## Core architecture

Agethrix is organized as a modular monolith:

```text
Browser
  │
  ▼
React frontend
  │
  │ HTTP API
  ▼
FastAPI backend
  │
  ├── Authentication and user accounts
  ├── Agent management
  ├── Agent specification and builds
  ├── Encrypted provider credentials
  ├── Conversation runtime
  └── Background job processing
       │
       ├── PostgreSQL
       └── Groq provider
```

The frontend provides the user experience, while the backend owns
authentication, authorization, persistence, provider access and agent
execution. Long-running build jobs are processed by a separate worker so the
API does not need to perform all build work inside a browser request.

## Repository structure

```text
Agethrix/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── auth.py          Authentication endpoints
│   │   │   ├── agents.py        Agent management endpoints
│   │   │   ├── builds.py        Build lifecycle endpoints
│   │   │   ├── chat.py          Conversation endpoints
│   │   │   ├── credentials.py   Provider credential endpoints
│   │   │   └── health.py        Service health endpoints
│   │   ├── core/
│   │   │   └── config.py        Application configuration
│   │   ├── database/
│   │   │   └── session.py       SQLAlchemy engine and sessions
│   │   ├── models/
│   │   │   ├── auth.py          Users and authentication tokens
│   │   │   ├── agents.py        Agent records
│   │   │   ├── builds.py        Deployments, configurations and jobs
│   │   │   └── conversations.py Conversation threads and messages
│   │   ├── schemas/
│   │   │   ├── auth.py          Authentication payloads
│   │   │   ├── agents.py        Agent payloads
│   │   │   ├── chat.py          Chat payloads
│   │   │   └── spec.py          Strict agent specification
│   │   ├── services/
│   │   │   ├── auth.py          Passwords and token services
│   │   │   ├── builder.py       Agent build orchestration
│   │   │   ├── encryption.py    Provider key encryption
│   │   │   ├── groq_client.py   Groq adapter
│   │   │   └── model_router.py  Model capability and budget routing
│   │   └── workers/
│   │       ├── handlers.py      Background job handlers
│   │       ├── job_worker.py    Claim, lease and retry logic
│   │       └── runner.py        Worker process entry point
│   ├── migrations/
│   │   └── versions/            PostgreSQL schema and RLS reference
│   ├── scripts/                 Maintenance scripts
│   ├── tests/                   Backend tests
│   └── main.py                  FastAPI application entry point
├── frontend/
│   ├── public/                  Favicon and web manifest
│   ├── src/
│   │   ├── components/          Shared and workspace components
│   │   ├── context/             Authentication state
│   │   ├── layouts/              Application shell and navigation
│   │   ├── pages/                Landing, auth, dashboard and workspace pages
│   │   ├── routes/               Protected route handling
│   │   ├── services/             API client and typed API methods
│   │   └── styles/               Agethrix design tokens and global styles
│   ├── index.html                Browser metadata and SEO information
│   └── package.json              Frontend dependencies and scripts
├── docs/
│   ├── architecture.md           System architecture
│   ├── database-design.md        Data model and isolation design
│   ├── api-documentation.md      API reference
│   ├── deployment-guide.md       Deployment documentation
│   └── PROGRESS.md               Implementation status
├── .github/workflows/             Continuous integration
├── render.yaml                   API and worker deployment definition
└── README.md                     Project overview
```

## Data ownership and isolation

Each user owns their credentials, agents, deployments and conversations.
Conversation data is scoped by:

1. Authenticated user
2. Agent
3. Conversation thread

This prevents one user from reading another user's data and prevents
conversations from different agents being mixed. Provider credentials are
encrypted by the backend and exposed only as masked values.

## Current platform experience

The implemented platform supports account authentication, encrypted provider
credentials, agent creation, natural-language agent building, durable build
jobs, individual agent workspaces, formatted chat responses, persistent
conversation history, separate chat threads and chat deletion.

The frontend presents Agethrix as a single cohesive platform while the
individual agent remains the primary identity inside its own workspace.

**Powered by Agethrix — From Intent to Intelligence.**
