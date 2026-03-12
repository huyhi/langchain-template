from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[UUID] = None
