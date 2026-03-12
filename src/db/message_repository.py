from uuid import UUID

from sqlmodel import Session, select

from db.models import Message
from db.thread_repository import thread_update_timestamp
from model.chat import MessageRole


def message_create(
    session: Session, thread_id: UUID, role: MessageRole, content: str
) -> Message:
    message = Message(
        thread_id=thread_id,
        role=role.value,
        content=content,
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


def message_list_all(session: Session, thread_id: UUID) -> list[Message]:
    statement = (
        select(Message)
        .where(Message.thread_id == thread_id)
        .order_by(Message.created_at)
    )
    return list(session.exec(statement).all())
