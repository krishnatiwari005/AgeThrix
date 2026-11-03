from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agents import Agent
from app.models.builds import AgentDeployment, Job
from app.services.builder import execute_build_deployment
from app.services.groq_client import GroqProviderError
from app.workers.job_worker import RetryableJobError


def handle_agent_build(db: Session, job: Job) -> None:
    agent = db.get(Agent, job.agent_id)
    if agent is None:
        raise RetryableJobError("Agent no longer exists")
    deployment = db.scalar(
        select(AgentDeployment)
        .where(
            AgentDeployment.agent_id == agent.id,
            AgentDeployment.owner_id == job.owner_id,
            AgentDeployment.status.in_(("queued", "failed", "awaiting_credentials")),
        )
        .order_by(AgentDeployment.created_at.desc())
    )
    if deployment is None:
        raise RetryableJobError("Build deployment no longer exists")
    try:
        execute_build_deployment(
            db,
            agent,
            UUID(str(job.owner_id)),
            deployment,
            str(job.payload.get("prompt", "")),
        )
    except (ValueError, GroqProviderError) as error:
        raise RetryableJobError(str(error)) from error
