"""Offline chat endpoint — POST returns plain JSON; SSE variant streams chunks."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.rate_limit import limiter
from app.models.user import User
from app.services import chat_service


router = APIRouter(prefix="/chat", tags=["chat"])


class ChatQueryIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    context_filters: dict[str, Any] | None = None
    stream: bool = False


class ChatQueryOut(BaseModel):
    answer: str
    source: str


@router.post("/query", response_model=ChatQueryOut)
@limiter.limit(settings.rate_limit_chat)
async def query(
    payload: ChatQueryIn,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ChatQueryOut | StreamingResponse:
    if payload.stream:
        async def gen():
            async for chunk in chat_service.stream_answer(db, message=payload.message, filters=payload.context_filters):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")
    res = await chat_service.answer(db, message=payload.message, filters=payload.context_filters)
    return ChatQueryOut(**res)
