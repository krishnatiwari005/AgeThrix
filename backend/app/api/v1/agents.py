from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.auth import current_user
from app.services.auth import decode_access_token
from app.core.config import settings
from app.database.session import get_db
from app.models.agents import Agent
from app.models.builds import AgentConfiguration
from app.models.auth import User
from app.schemas.agents import AgentCreate, AgentResponse, AgentUpdate
from app.services.slugs import generate_slug

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


def agent_response(agent: Agent, db: Session) -> AgentResponse:
    response = AgentResponse.model_validate(agent, from_attributes=True)
    configuration = db.scalar(
        select(AgentConfiguration).where(
            AgentConfiguration.agent_id == agent.id,
            AgentConfiguration.is_current.is_(True),
        )
    )
    preferences = configuration.spec.get("model_preferences", {}) if configuration else {}
    preferred_models = preferences.get("preferred_models", []) if isinstance(preferences, dict) else []
    response.model_name = str(preferred_models[0]) if preferred_models else (
        "openai/gpt-oss-20b" if configuration else None
    )
    return response


def get_owned_agent(agent_id: UUID, user: User, db: Session) -> Agent:
    agent = db.scalar(
        select(Agent).where(Agent.id == agent_id, Agent.owner_id == user.id)
    )
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


def unique_slug(name: str, db: Session) -> str:
    for _ in range(5):
        slug = generate_slug(name)
        if db.scalar(select(Agent.id).where(Agent.slug == slug)) is None:
            return slug
    raise HTTPException(status_code=503, detail="Unable to allocate agent URL")


@router.post("", response_model=AgentResponse, status_code=201)
def create_agent(
    payload: AgentCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> AgentResponse:
    count = db.scalar(select(func.count()).select_from(Agent).where(Agent.owner_id == user.id)) or 0
    if count >= settings.max_agents_per_user:
        raise HTTPException(status_code=409, detail="Agent limit reached")
    agent = Agent(
        owner_id=user.id,
        name=payload.name.strip(),
        description=payload.description,
        slug=unique_slug(payload.name, db),
        access_mode=payload.access_mode,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent_response(agent, db)


@router.get("", response_model=list[AgentResponse])
def list_agents(
    user: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[AgentResponse]:
    agents = db.scalars(
        select(Agent).where(Agent.owner_id == user.id).order_by(Agent.created_at.desc())
    ).all()
    return [agent_response(agent, db) for agent in agents]


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> AgentResponse:
    return agent_response(get_owned_agent(agent_id, user, db), db)


@router.get("/by-slug/{slug}", response_model=AgentResponse)
def get_agent_by_slug(
    slug: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> AgentResponse:
    agent = db.scalar(select(Agent).where(Agent.slug == slug))
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.access_mode == "private":
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")
        try:
            owner_id = decode_access_token(authorization[7:])
        except (jwt.InvalidTokenError, ValueError):
            raise HTTPException(status_code=401, detail="Authentication required") from None
        if agent.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="Agent not found")
    return agent_response(agent, db)


@router.patch("/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: UUID,
    payload: AgentUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> AgentResponse:
    agent = get_owned_agent(agent_id, user, db)
    if payload.name is not None:
        agent.name = payload.name.strip()
    if payload.description is not None:
        agent.description = payload.description
    if payload.access_mode is not None:
        agent.access_mode = payload.access_mode
    db.commit()
    db.refresh(agent)
    return agent_response(agent, db)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(
    agent_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> None:
    agent = get_owned_agent(agent_id, user, db)
    db.delete(agent)
    db.commit()
