
"""
Gemini-powered chat orchestration for SpendWise AI.

Gemini can request approved finance tools, but only the backend
executes them. All conversations are scoped to the authenticated user.
"""

import logging
import time
from uuid import UUID

from google.genai import types
from sqlalchemy.orm import Session

from app.services.ai_conversation_service import (
    create_conversation,
    get_conversation,
    get_conversation_messages,
    save_message,
)
from app.services.ai_tool_registry import FINANCE_TOOL, execute_finance_tool
from app.services.gemini_service import get_gemini_client, get_gemini_model


logger = logging.getLogger("uvicorn.error")


SYSTEM_INSTRUCTION = """
You are SpendWise AI, a helpful personal finance assistant.

Your responsibilities:
- Answer questions about the user's financial activity.
- Explain spending patterns, budgets, account balances, and cash flow.
- Use the available finance tools whenever accurate financial data is needed.
- Never invent transactions, balances, budgets, or financial figures.
- Clearly distinguish actual financial data from general suggestions.
- Do not claim to have performed financial operations such as transferring
  money or editing transactions. You are a read-only financial assistant.
- Keep answers clear, practical, and easy to understand.

Security rules:
- Only use the finance tools provided to you.
- Never request or expose passwords, API keys, or authentication tokens.
- Never assume another user's financial information is accessible.
"""


MAX_TOOL_ROUNDS = 5


def _build_gemini_history(messages):
    """Convert persisted messages into Gemini-compatible content."""

    history = []

    for message in messages:
        role = "user" if message.role == "user" else "model"

        history.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=message.content)],
            )
        )

    return history


def send_chat_message(
    db: Session,
    user_id: UUID,
    message: str,
    conversation_id: UUID | None = None,
) -> dict:
    """
    Process a user message through Gemini and approved finance tools.

    The authenticated user_id is injected by the backend and is never
    accepted from Gemini's function-call arguments.
    """

    total_start = time.perf_counter()

    try:
        message = message.strip()

        if not message:
            raise ValueError("Message cannot be empty.")

        if len(message) > 10000:
            raise ValueError("Message cannot exceed 10,000 characters.")

        # Create a new conversation or verify ownership of an existing one.
        if conversation_id is None:
            conversation = create_conversation(
                db=db,
                user_id=user_id,
                title=message[:50],
            )
        else:
            conversation = get_conversation(
                db=db,
                user_id=user_id,
                conversation_id=conversation_id,
            )

            if conversation is None:
                raise ValueError("Conversation not found.")

        # Persist the user message before contacting Gemini.
        save_message(
            db=db,
            conversation=conversation,
            role="user",
            content=message,
        )

        # Load persisted history in chronological order.
        messages = get_conversation_messages(
            db=db,
            conversation_id=conversation.id,
        )

        contents = _build_gemini_history(messages)

        client = get_gemini_client()
        model = get_gemini_model()

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=[FINANCE_TOOL],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
            temperature=0.2,
        )

        tools_used = []
        final_response = None
        gemini_call_number = 0

        # Allow Gemini to request tools, receive their results, and respond.
        for round_number in range(1, MAX_TOOL_ROUNDS + 1):

            gemini_call_number += 1
            gemini_start = time.perf_counter()

            logger.info("Using Gemini model: %s", model)

            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )

            gemini_duration = time.perf_counter() - gemini_start

            logger.info(
                "Gemini API call #%d completed in %.2f seconds.",
                gemini_call_number,
                gemini_duration,
            )

            candidates = response.candidates or []

            if not candidates:
                raise RuntimeError(
                    "Gemini returned no response candidates."
                )

            model_content = candidates[0].content

            if model_content is None:
                raise RuntimeError("Gemini returned an empty response.")

            # Preserve the model's function-call response in temporary context.
            contents.append(model_content)

            function_calls = [
                part.function_call
                for part in (model_content.parts or [])
                if part.function_call is not None
            ]

            # No tool calls means Gemini has produced its final answer.
            if not function_calls:
                final_response = response.text

                if not final_response:
                    raise RuntimeError(
                        "Gemini returned an empty text response."
                    )

                break

            # Execute every requested function through our approved registry.
            for function_call in function_calls:

                tool_name = function_call.name
                arguments = dict(function_call.args or {})

                tool_start = time.perf_counter()

                try:
                    tool_result = execute_finance_tool(
                        tool_name=tool_name,
                        arguments=arguments,
                        db=db,
                        user_id=user_id,
                    )

                    tools_used.append(tool_name)

                except ValueError as exc:
                    # Return a controlled error to Gemini instead of
                    # executing an invalid or unapproved operation.
                    tool_result = {"error": str(exc)}

                tool_duration = time.perf_counter() - tool_start

                logger.info(
                    "Finance tool '%s' completed in %.2f seconds.",
                    tool_name,
                    tool_duration,
                )

                # Gemini expects function responses under the user role.
                contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_function_response(
                                name=tool_name,
                                response={"result": tool_result},
                            )
                        ],
                    )
                )

        if final_response is None:
            raise RuntimeError(
                "Gemini exceeded the maximum number of finance tool rounds."
            )

        # Persist the final assistant response.
        assistant_message = save_message(
            db=db,
            conversation=conversation,
            role="assistant",
            content=final_response,
            metadata={"tools_used": tools_used},
        )

        return {
            "conversation_id": str(conversation.id),
            "message_id": str(assistant_message.id),
            "response": final_response,
            "tools_used": tools_used,
        }

    finally:
        total_duration = time.perf_counter() - total_start

        logger.info(
            "Total AI chat processing time: %.2f seconds.",
            total_duration,
        )
