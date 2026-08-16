"""Copilot chat: a local-LLM assistant grounded in the user's own profile
and (optionally) a specific job posting they're looking at. Every reply
streams token-by-token from Ollama straight through to the client.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.integrations.ollama_client import OllamaClient
from app.models.chat import ChatMessage, ChatSession
from app.models.job import JobPosting
from app.models.profile import Profile

BASE_SYSTEM_PROMPT = (
    "You are the user's job search copilot, running locally on their own server. "
    "You help with resume feedback, interview prep, cover letters, understanding job "
    "match results, and general job-search strategy. Be concise, concrete, and honest - "
    "if the user's profile is missing something a role needs, say so plainly rather than "
    "being falsely encouraging. Never claim you submitted an application or contacted "
    "anyone on the user's behalf - you can only draft/advise; the user always takes "
    "real-world actions themselves."
)


def _build_system_prompt(profile: Profile | None, job_posting: JobPosting | None) -> str:
    parts = [BASE_SYSTEM_PROMPT]
    if profile is not None:
        parts.append(f"\nUSER'S PROFILE:\n{profile.searchable_text()[:3000]}")
    if job_posting is not None:
        parts.append(
            f"\nTHIS CONVERSATION IS ABOUT THIS JOB POSTING:\n"
            f"{job_posting.title} at {job_posting.company} ({job_posting.location})\n"
            f"{job_posting.description_text[:3000]}"
        )
    return "\n".join(parts)


async def get_or_create_session(
    db: AsyncSession, user_id: UUID, title: str, job_posting_id: UUID | None
) -> ChatSession:
    session = ChatSession(user_id=user_id, title=title, job_posting_id=job_posting_id)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def list_sessions(db: AsyncSession, user_id: UUID) -> list[ChatSession]:
    stmt = select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc())
    return list((await db.execute(stmt)).scalars().all())


async def get_session(db: AsyncSession, user_id: UUID, session_id: UUID) -> ChatSession | None:
    stmt = (
        select(ChatSession)
        .where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        .options(selectinload(ChatSession.messages))
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def delete_session(db: AsyncSession, user_id: UUID, session_id: UUID) -> bool:
    session = await get_session(db, user_id, session_id)
    if session is None:
        return False
    await db.delete(session)
    await db.commit()
    return True


async def stream_reply(
    db: AsyncSession, session: ChatSession, profile: Profile | None, user_content: str
) -> AsyncIterator[str]:
    """Persists the user's message immediately, streams the assistant's
    reply chunk by chunk, then persists the full assistant message once
    streaming completes.
    """
    db.add(ChatMessage(session_id=session.id, role="user", content=user_content))
    await db.commit()

    job_posting = None
    if session.job_posting_id is not None:
        job_posting = await db.get(JobPosting, session.job_posting_id)

    history_stmt = select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at)
    history = list((await db.execute(history_stmt)).scalars().all())

    messages = [{"role": "system", "content": _build_system_prompt(profile, job_posting)}]
    messages += [{"role": m.role, "content": m.content} for m in history]

    client = OllamaClient()
    full_reply = ""
    async for chunk in client.chat_stream(messages):
        full_reply += chunk
        yield chunk

    db.add(ChatMessage(session_id=session.id, role="assistant", content=full_reply))
    await db.commit()
