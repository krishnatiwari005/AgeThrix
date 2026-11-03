from uuid import uuid4

from app.database.session import SessionLocal
from app.models.agents import Agent
from app.models.auth import User
from app.models.builds import Job
from app.workers.job_worker import JobWorker, RetryableJobError


def test_worker_claims_and_completes_job() -> None:
    with SessionLocal() as db:
        user = User(email=f"worker-{uuid4()}@example.com", password_hash="hash")
        db.add(user)
        db.flush()
        agent = Agent(
            owner_id=user.id,
            name="Worker agent",
            slug=f"worker-{uuid4().hex[:8]}",
        )
        db.add(agent)
        db.flush()
        job = Job(
            owner_id=user.id,
            agent_id=agent.id,
            type="test",
            payload={"value": 1},
        )
        db.add(job)
        db.commit()
        job_id = job.id

    seen: list[str] = []

    def handler(db, claimed_job) -> None:
        seen.append(str(claimed_job.id))

    worker = JobWorker(SessionLocal, {"test": handler})
    assert worker.run_once() is True
    assert seen == [str(job_id)]
    with SessionLocal() as db:
        assert db.get(Job, job_id).status == "completed"


def test_worker_requeues_retryable_job_until_limit() -> None:
    with SessionLocal() as db:
        user = User(email=f"retry-{uuid4()}@example.com", password_hash="hash")
        db.add(user)
        db.flush()
        agent = Agent(
            owner_id=user.id,
            name="Retry agent",
            slug=f"retry-{uuid4().hex[:8]}",
        )
        db.add(agent)
        db.flush()
        job = Job(
            owner_id=user.id,
            agent_id=agent.id,
            type="retry",
            payload={},
        )
        db.add(job)
        db.commit()
        job_id = job.id

    def handler(db, claimed_job) -> None:
        raise RetryableJobError("temporary provider failure")

    worker = JobWorker(SessionLocal, {"retry": handler}, max_attempts=2)
    assert worker.run_once() is True
    with SessionLocal() as db:
        assert db.get(Job, job_id).status == "queued"
    assert worker.run_once() is True
    with SessionLocal() as db:
        stored = db.get(Job, job_id)
        assert stored.status == "failed"
        assert stored.payload["last_error"] == "temporary provider failure"
