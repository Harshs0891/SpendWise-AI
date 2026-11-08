
"""
Gemini provider initialization for SpendWise AI.

This module centralizes Gemini client creation so that
the rest of the application does not manage API keys
or instantiate separate clients.
"""

from functools import lru_cache

from google import genai

from app.core.config import get_settings


@lru_cache
def get_gemini_client() -> genai.Client:
    """
    Return a cached Gemini client.

    The API key is read from backend configuration,
    never from a user request or an AI-generated argument.
    """

    settings = get_settings()

    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Add it to the backend .env file."
        )

    return genai.Client(api_key=settings.gemini_api_key)


def get_gemini_model() -> str:
    """Return the configured Gemini model ID."""

    return get_settings().gemini_model
