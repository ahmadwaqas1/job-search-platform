from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionOut,
    ChatSessionSummaryOut,
    SendMessageRequest,
)
from app.services import chat_service
from app.services.profile_service import get_or_create_profile

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/sessions", response_model=list[ChatSessionSummaryOut])
async def list_sessions(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await chat_service.list_sessions(db, user.id)


@router.post("/sessions", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: ChatSessionCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    session = await chat_service.get_or_create_session(db, user.id, payload.title, payload.job_posting_id)
    return await chat_service.get_session(db, user.id, session.id)


@router.get("/sessions/{session_id}", response_model=ChatSessionOut)
async def get_session(
    session_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    session = await chat_service.get_session(db, user.id, session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat session not found.")
    return session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    ok = await chat_service.delete_session(db, user.id, session_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat session not found.")


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: UUID,
    payload: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await chat_service.get_session(db, user.id, session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat session not found.")
    profile = await get_or_create_profile(db, user)

    return StreamingResponse(
        chat_service.stream_reply(db, session, profile, payload.content),
        media_type="text/plain",
    )
