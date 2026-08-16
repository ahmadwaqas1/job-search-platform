"""RQ worker process entrypoint. Run with `python -m app.workers.worker`.
Listens on both queues - `llm` is listed first so LLM-bound jobs get
priority when both have pending work, but `default` (ingestion/upserts)
still gets serviced whenever `llm` is empty.
"""
import structlog
from rq import Worker

from app.workers.queue import get_redis

log = structlog.get_logger()

if __name__ == "__main__":
    log.info("worker.starting", queues=["llm", "default"])
    worker = Worker(["llm", "default"], connection=get_redis())
    worker.work(with_scheduler=False)
