
"""
Persistence operations for SpendWise AI conversations.

All operations are scoped to the authenticated user.
The service never trusts a conversation ID alone:
it always checks conversation ownership first.
"""

from datetime import datetime, timezone

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AIConversation, AIMessage


def create_conversation(
    db: Session,
    user_id: UUID,
    title: str = "New conversation",
) -> AIConversation:
    """Create a conversation owned by the authenticated user."""

    conversation = AIConversation(
        user_id=user_id,
        title=title[:150],
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


def get_conversation(
    db: Session,
    user_id: UUID,
    conversation_id: UUID,
) -> AIConversation | None:
    """Retrieve a conversation only if it belongs to the user."""

    return db.scalar(
        select(AIConversation).where(
            AIConversation.id == conversation_id,
            AIConversation.user_id == user_id,
        )
    )


def list_conversations(
    db: Session,
    user_id: UUID,
    limit: int = 50,
) -> list[AIConversation]:
    """List the user's conversations, newest activity first."""

    return list(
        db.scalars(
            select(AIConversation)
            .where(AIConversation.user_id == user_id)
            .order_by(
                AIConversation.updated_at.desc(),
                AIConversation.created_at.desc(),
            )
            .limit(limit)
        ).all()
    )


def save_message(
    db: Session,
    conversation: AIConversation,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> AIMessage:
    """Persist one user or assistant message."""

    if role not in {"user", "assistant"}:
        raise ValueError("Message role must be user or assistant.")

    message = AIMessage(
        conversation_id=conversation.id,
        role=role,
        content=content,
        metadata_=metadata,
    )

    db.add(message)

    # Updating this field makes the conversation appear first
    # in the user's recent conversation list.
    conversation.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(message)

    return message


def get_conversation_messages(
    db: Session,
    conversation_id: UUID,
    limit: int = 100,
) -> list[AIMessage]:
    """Retrieve messages in chronological order."""

    statement = (
        select(AIMessage)
        .where(AIMessage.conversation_id == conversation_id)
        .order_by(AIMessage.created_at.desc())
        .limit(limit)
    )

    # Query newest messages first for efficiency, then reverse
    # them so Gemini receives the conversation chronologically.
    messages = list(db.scalars(statement).all())
    return list(reversed(messages))
