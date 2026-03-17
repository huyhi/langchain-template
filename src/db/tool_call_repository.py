import json
from uuid import UUID

from sqlmodel import Session, select

from db.models import ToolCall


def tool_call_create(
    session: Session,
    thread_id: UUID,
    tool_call_id: str,
    tool_name: str,
    input: dict | str,
    output: str,
) -> ToolCall:
    input_str = (
        json.dumps(input, ensure_ascii=False)
        if isinstance(input, dict)
        else str(input)
    )
    record = ToolCall(
        thread_id=thread_id,
        tool_call_id=tool_call_id,
        tool_name=tool_name,
        input=input_str,
        output=output,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def tool_call_list(session: Session, thread_id: UUID) -> list[ToolCall]:
    statement = (
        select(ToolCall)
        .where(ToolCall.thread_id == thread_id)
        .order_by(ToolCall.created_at)
    )
    return list(session.exec(statement).all())
