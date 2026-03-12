from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from db import repository
from db.database import get_session
from db.models import Message, Thread

router = APIRouter(prefix="/api/v1/threads", tags=["threads"])


@router.post("/", response_model=Thread, status_code=201)
def create_thread(session: Session = Depends(get_session)) -> Thread:
    return repository.thread_create(session)


@router.get("/", response_model=list[Thread])
def list_threads(session: Session = Depends(get_session)) -> list[Thread]:
    return repository.thread_list_all(session)


@router.get("/{thread_id}", response_model=Thread)
def get_thread(thread_id: UUID, session: Session = Depends(get_session)) -> Thread:
    thread = repository.thread_get(session, thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@router.get("/{thread_id}/messages", response_model=list[Message])
def list_messages(
    thread_id: UUID, session: Session = Depends(get_session)
) -> list[Message]:
    thread = repository.thread_get(session, thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return repository.message_list_all(session, thread_id)
