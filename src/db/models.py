from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Index
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
    tool_calls: list["ToolCall"] = Relationship(back_populates="thread")


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
        Index("ix_message_thread_id_updated_at", "thread_id", "updated_at"),
        {"sqlite_autoincrement": True},
    )


class ToolCall(SQLModel, table=True):
    __tablename__ = "tool_call"

    inc_id: Optional[int] = Field(default=None, primary_key=True)
    id: UUID = Field(default_factory=uuid4, index=True, unique=True)
    thread_id: UUID = Field(foreign_key="thread.id", index=True)
    tool_call_id: str = Field(index=True)  # ID assigned by the LLM
    tool_name: str
    input: str  # JSON-serialised input arguments
    output: str  # raw output text returned by the tool
    created_at: datetime = Field(default_factory=_utcnow)

    thread: Optional[Thread] = Relationship(back_populates="tool_calls")

    __table_args__ = (
        Index("ix_tool_call_thread_id_created_at", "thread_id", "created_at"),
        {"sqlite_autoincrement": True},
    )
