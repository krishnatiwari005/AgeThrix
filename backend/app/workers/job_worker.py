from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.builds import Job

JobHandler = Callable[[Session, Job], None]


class JobWorker:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        handlers: dict[str, JobHandler],
        lease_seconds: int = 300,
        max_attempts: int = 3,
    ) -> None:
        self.session_factory = session_factory
        self.handlers = handlers
        self.lease_seconds = lease_seconds
        self.max_attempts = max_attempts

    def claim_next(self, db: Session) -> UUID | None:
        now = datetime.now(UTC)
        job = db.scalar(
            select(Job)
            .where(
                Job.status == "queued",
                or_(Job.locked_until.is_(None), Job.locked_until < now),
                Job.attempts < self.max_attempts,
            )
            .order_by(Job.created_at)
            .with_for_update(skip_locked=True)
        )
        if job is None:
            return None
        job.status = "running"
        job.attempts += 1
        job.locked_until = now + timedelta(seconds=self.lease_seconds)
        db.commit()
        return job.id

    def run_once(self) -> bool:
        with self.session_factory() as claim_db:
            job_id = self.claim_next(claim_db)
        if job_id is None:
            return False

        with self.session_factory() as db:
            job = db.get(Job, job_id)
            if job is None:
                return True
            handler = self.handlers.get(job.type)
            if handler is None:
                job.status = "failed"
                job.locked_until = None
                db.commit()
                return True
            try:
                handler(db, job)
            except RetryableJobError as error:
                job.status = "queued" if job.attempts < self.max_attempts else "failed"
                job.payload = {**job.payload, "last_error": str(error)}
                job.locked_until = None
                db.commit()
            else:
                job.status = "completed"
                job.locked_until = None
                db.commit()
        return True


class RetryableJobError(RuntimeError):
    pass
