from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.agents import get_owned_agent
from app.api.v1.auth import current_user
from app.database.session import get_db
from app.models.auth import User
from app.models.builds import AgentConfiguration, AgentDeployment, Job
from app.schemas.builds import BuildRequest, BuildResponse, BuildStatus, BuildStatusResponse
from app.schemas.spec import AgentSpec
from app.services.builder import build_agent, execute_build_deployment
from app.services.groq_client import GroqProviderError

router = APIRouter(prefix="/api/v1/agents", tags=["builds"])


def response_for(deployment: AgentDeployment, spec: AgentSpec | None = None) -> BuildStatusResponse:
    return BuildStatusResponse(
        deployment_id=deployment.id,
        status=cast(BuildStatus, deployment.status),
        stage=deployment.stage,
        progress=deployment.progress,
        safe_error=deployment.safe_error,
        updated_at=deployment.updated_at,
        spec=spec,
    )


@router.post("/{agent_id}/build", response_model=BuildResponse, status_code=status.HTTP_202_ACCEPTED)
def start_build(
    agent_id: UUID,
    payload: BuildRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> BuildResponse:
    agent = get_owned_agent(agent_id, user, db)
    if agent.status == "building":
        raise HTTPException(status_code=409, detail="Agent build already in progress")
    deployment = build_agent(db, agent, user.id, payload.prompt, payload.model_preference)
    db.commit()
    db.refresh(deployment)
    return response_for(deployment)


@router.post(
    "/{agent_id}/build/resume",
    response_model=BuildStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def resume_build(
    agent_id: UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> BuildStatusResponse:
    agent = get_owned_agent(agent_id, user, db)
    deployment = db.scalar(
        select(AgentDeployment)
        .where(
            AgentDeployment.agent_id == agent.id,
            AgentDeployment.owner_id == user.id,
        )
        .order_by(AgentDeployment.created_at.desc())
    )
    if deployment is None:
        raise HTTPException(status_code=404, detail="Build not found")
    job = db.scalar(
        select(Job)
        .where(
            Job.agent_id == agent.id,
            Job.owner_id == user.id,
            Job.type == "agent_build",
        )
        .order_by(Job.created_at.desc())
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Build job not found")
    prompt = str(job.payload.get("prompt", ""))
    try:
        execute_build_deployment(db, agent, user.id, deployment, prompt)
    except (ValueError, GroqProviderError):
        deployment.status = "failed"
        deployment.stage = "configuring_models"
        deployment.safe_error = "The provider could not complete the build. Check the credential and retry."
        agent.status = "failed"
    job.attempts += 1
    job.status = "completed" if deployment.status == "active" else deployment.status
    db.commit()
    db.refresh(deployment)
    configuration = db.scalar(
        select(AgentConfiguration).where(
            AgentConfiguration.agent_id == agent.id,
            AgentConfiguration.is_current.is_(True),
        )
    )
    spec = AgentSpec.model_validate(configuration.spec) if configuration else None
    return response_for(deployment, spec)


@router.get("/{agent_id}/build-status", response_model=BuildStatusResponse)
def build_status(
    agent_id: UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> BuildStatusResponse:
    agent = get_owned_agent(agent_id, user, db)
    deployment = db.scalar(
        select(AgentDeployment)
        .where(
            AgentDeployment.agent_id == agent.id,
            AgentDeployment.owner_id == user.id,
        )
        .order_by(AgentDeployment.created_at.desc())
    )
    if deployment is None:
        raise HTTPException(status_code=404, detail="Build not found")
    configuration = db.scalar(
        select(AgentConfiguration).where(
            AgentConfiguration.agent_id == agent.id,
            AgentConfiguration.is_current.is_(True),
        )
    )
    spec = AgentSpec.model_validate(configuration.spec) if configuration else None
    return response_for(deployment, spec)
