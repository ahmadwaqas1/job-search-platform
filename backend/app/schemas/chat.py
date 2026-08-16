from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ChatSessionCreate(BaseModel):
    title: str = "New conversation"
    job_posting_id: UUID | None = None


class ChatMessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionOut(BaseModel):
    id: UUID
    title: str
    job_posting_id: UUID | None
    created_at: datetime
    messages: list[ChatMessageOut]

    model_config = {"from_attributes": True}


class ChatSessionSummaryOut(BaseModel):
    id: UUID
    title: str
    job_posting_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    content: str
