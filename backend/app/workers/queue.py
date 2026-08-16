"""Shared RQ queue setup, imported by both the FastAPI app (to enqueue work)
and the worker process (to consume it). Two queues so slow LLM-bound tasks
(extraction, embeddings, match explanations, draft generation, chat) never
starve quick ingestion/upsert work.

Note on how tasks get enqueued: routers call things like
    default_queue().enqueue("app.workers.cv_tasks.parse_cv_document", str(doc.id))
i.e. a dotted STRING naming the task function, not the function object
itself. This is a normal RQ pattern, not a typo - it lets the API process
enqueue work without importing the worker modules (which pull in heavier
sync-only dependencies), and lets the worker process resolve+import that
path only when it actually runs the job.
"""
from redis import Redis
from rq import Queue

from app.config import get_settings

settings = get_settings()

_redis_conn: Redis | None = None


def get_redis() -> Redis:
    global _redis_conn
    if _redis_conn is None:
        _redis_conn = Redis.from_url(settings.redis_url)
    return _redis_conn


def default_queue() -> Queue:
    return Queue("default", connection=get_redis())


def llm_queue() -> Queue:
    return Queue("llm", connection=get_redis())
