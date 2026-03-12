from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from db.models import Thread


def thread_create(session: Session, title: Optional[str] = None) -> Thread:
    thread = Thread(title=title)
    session.add(thread)
    session.commit()
    session.refresh(thread)
    return thread


def thread_get(session: Session, thread_id: UUID) -> Optional[Thread]:
    return session.get(Thread, thread_id)


def thread_list_all(session: Session) -> list[Thread]:
    statement = select(Thread).order_by(Thread.created_at.desc())
    return list(session.exec(statement).all())


def thread_update_timestamp(session: Session, thread_id: UUID) -> None:
    thread = session.get(Thread, thread_id)
    if thread:
        thread.updated_at = datetime.now(timezone.utc)
        session.add(thread)
        session.commit()


def thread_update_title(session: Session, thread_id: UUID, title: str) -> None:
    statement = select(Thread).where(Thread.id == thread_id)
    thread = session.exec(statement).first()
    if thread:
        thread.title = title
        thread.updated_at = datetime.now(timezone.utc)
        session.add(thread)
        session.commit()
