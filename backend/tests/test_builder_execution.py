from uuid import uuid4

from app.database.session import SessionLocal
from app.models.agents import Agent
from app.models.auth import User
from app.models.builds import AgentDeployment
from app.services.builder import run_build_job
from app.services.groq_client import FakeGroqClient


def test_fake_builder_job_activates_agent_and_persists_spec() -> None:
    with SessionLocal() as db:
        user = User(email=f"run-{uuid4()}@example.com", password_hash="hash")
        db.add(user)
        db.flush()
        agent = Agent(
            owner_id=user.id,
            name="Builder",
            slug=f"builder-{uuid4().hex[:6]}",
        )
        db.add(agent)
        db.flush()
        deployment = AgentDeployment(
            agent_id=agent.id,
            owner_id=user.id,
            status="queued",
            stage="understanding",
            progress=5,
        )
        db.add(deployment)
        db.flush()

        run_build_job(
            db,
            agent,
            user.id,
            deployment,
            FakeGroqClient(),
            "test-model",
            "Create a helpful assistant.",
        )
        db.commit()

        assert deployment.status == "active"
        assert deployment.progress == 100
        assert agent.status == "active"
