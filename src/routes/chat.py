from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from db import repository
from db.database import get_session
from model.chat import ChatRequest, MessageRole
from service.chat import generate_and_set_title, get_or_create_thread, stream_agent

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/streaming")
async def chat_streaming(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
) -> StreamingResponse:
    thread = get_or_create_thread(session, request.thread_id)

    repository.message_create(session, thread.id, MessageRole.USER, request.message)

    if not thread.title:
        background_tasks.add_task(generate_and_set_title, request.message, thread.id)

    return StreamingResponse(
        stream_agent(request.message, thread.id, str(uuid4())),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
