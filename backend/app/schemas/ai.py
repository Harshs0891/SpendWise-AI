
"""
Pydantic schemas for SpendWise AI chat APIs.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AIChatRequest(BaseModel):
    """Request body for sending a message to SpendWise AI."""

    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The user's message.",
    )

    conversation_id: UUID | None = Field(
        default=None,
        description="Existing conversation ID. Omit to start a new conversation.",
    )


class AIChatResponse(BaseModel):
    """Response returned after processing a chat message."""

    conversation_id: UUID
    message_id: UUID
    response: str
    tools_used: list[str]


class AIConversationResponse(BaseModel):
    """Summary of a saved AI conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class AIMessageResponse(BaseModel):
    """Individual message within a conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class AIConversationDetailResponse(AIConversationResponse):
    """Conversation summary together with its message history."""

    messages: list[AIMessageResponse]
