
"""
FastAPI endpoints for SpendWise AI conversations.

Every endpoint requires authentication and scopes data
to the currently authenticated user.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from google.genai.errors import APIError

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.ai import (
    AIChatRequest,
    AIChatResponse,
    AIConversationDetailResponse,
    AIConversationResponse,
)
from app.services.ai_chat_service import send_chat_message
from app.services.ai_conversation_service import (
    get_conversation,
    get_conversation_messages,
    list_conversations,
)
from app.models import AIConversation

from datetime import date

from app.services.ai_insights_service import get_spending_insights

from app.services.ai_budget_advisor import get_smart_budget_advice
from app.services.ai_monthly_report_service import generate_monthly_report


router = APIRouter(prefix="/ai", tags=["AI Assistant"])


@router.post("/chat", response_model=AIChatResponse)
def chat(
    payload: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message to SpendWise AI."""

    try:
        return send_chat_message(
            db=db,
            user_id=current_user.id,
            message=payload.message,
            conversation_id=payload.conversation_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except APIError as exc:
        # Gemini may temporarily be unavailable or reject a request.
        provider_status = getattr(exc, "code", None)

        if provider_status == 503:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SpendWise AI is temporarily unavailable. Please try again shortly.",
            ) from exc

        print(
            f"Gemini API error: status={exc.code}, "
            f"message={exc.message}"
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI provider could not process your request.",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI assistant could not process your message.",
        ) from exc


@router.get(
    "/conversations",
    response_model=list[AIConversationResponse],
)
def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List conversations belonging to the authenticated user."""

    return list_conversations(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=AIConversationDetailResponse,
)
def get_conversation_detail(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a conversation and its messages after ownership validation."""

    conversation = get_conversation(
        db=db,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    messages = get_conversation_messages(
        db=db,
        conversation_id=conversation.id,
    )

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": messages,
    }


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a conversation owned by the authenticated user."""

    conversation = get_conversation(
        db=db,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    db.delete(conversation)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/insights/spending")
def spending_insights(
    reference_date: date | None = None,
    currency: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Return deterministic spending insights for the authenticated user.

    Optional query parameters:
    - reference_date: Any date within the month to analyze.
    - currency: Restrict results to one currency.
    """

    return get_spending_insights(
        db=db,
        user_id=current_user.id,
        reference_date=reference_date,
        currency=currency,
    )


@router.get("/advisor/budget")
def budget_advisor(
    reference_date: date | None = None,
    currency: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return personalized, read-only budget recommendations."""

    return get_smart_budget_advice(
        db=db,
        user_id=current_user.id,
        reference_date=reference_date,
        currency=currency,
    )


@router.get("/reports/monthly")
def monthly_financial_report(
    reference_date: date | None = None,
    currency: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate a monthly financial report."""

    return generate_monthly_report(
        db=db,
        user_id=current_user.id,
        reference_date=reference_date,
        currency=currency,
    )