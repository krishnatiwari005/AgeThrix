import time
import os

from app.database.session import SessionLocal
from app.workers.handlers import handle_agent_build
from app.workers.job_worker import JobWorker


def create_worker() -> JobWorker:
    return JobWorker(
        session_factory=SessionLocal,
        handlers={"agent_build": handle_agent_build},
        lease_seconds=int(os.getenv("WORKER_LEASE_SECONDS", "300")),
        max_attempts=int(os.getenv("WORKER_MAX_ATTEMPTS", "3")),
    )


def run_forever(poll_seconds: float | None = None) -> None:
    worker = create_worker()
    interval = poll_seconds if poll_seconds is not None else float(
        os.getenv("WORKER_POLL_SECONDS", "2")
    )
    while True:
        if not worker.run_once():
            time.sleep(interval)


if __name__ == "__main__":
    run_forever()
