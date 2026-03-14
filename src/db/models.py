from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Thread(SQLModel, table=True):
    inc_id: Optional[int] = Field(default=None, primary_key=True)
    id: UUID = Field(default_factory=uuid4, index=True, unique=True)
    title: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    messages: list["Message"] = Relationship(back_populates="thread")


class Message(SQLModel, table=True):
    inc_id: Optional[int] = Field(default=None, primary_key=True)
    id: UUID = Field(default_factory=uuid4, index=True, unique=True)
    thread_id: UUID = Field(foreign_key="thread.id", index=True)
    role: str  # "user" | "assistant"
    content: str
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(
        default_factory=_utcnow, index=True
    )  # <-- Add indexed updated_at

    thread: Optional[Thread] = Relationship(back_populates="messages")

    __table_args__ = (
        # Composite index to optimize queries filtering by thread_id and ordering by updated_at DESC
        # As seen in message_list_latest
        {"sqlite_autoincrement": True},
        {
            "indexes": [
                # Composite index for the query:
                # select(Message).where(Message.thread_id == thread_id).order_by(Message.updated_at.desc()).limit(limit)
                ("ix_message_thread_id_updated_at", "thread_id", "updated_at"),
            ]
        },
    )
