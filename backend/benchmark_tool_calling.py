"""
Verify Gemini 3.5 Flash Lite function-calling support.
This test does not execute finance tools or access the database.
"""

from google import genai
from google.genai import types

from app.services.gemini_service import get_gemini_client
from app.services.ai_tool_registry import FINANCE_TOOL


MODEL = "gemini-3.5-flash-lite"


def benchmark_tool_calling():
    client = get_gemini_client()

    print(f"\nTesting function calling: {MODEL}")

    start = __import__("time").perf_counter()

    response = client.models.generate_content(
        model=MODEL,
        contents=(
            "Show my financial overview for November 2026. "
            "Use get_financial_overview with start_date 2026-11-01 "
            "and end_date 2026-11-30."
        ),
        config=types.GenerateContentConfig(
            tools=[FINANCE_TOOL],
            automatic_function_calling=(
                types.AutomaticFunctionCallingConfig(disable=True)
            ),
            temperature=0.2,
        ),
    )

    elapsed = __import__("time").perf_counter() - start

    print(f"\nLatency: {elapsed:.2f} seconds")

    function_calls = response.function_calls or []

    if function_calls:
        print("\nFunction calling supported!")
        for call in function_calls:
            print(f"Function: {call.name}")
            print(f"Arguments: {call.args}")
    else:
        print("\nNo function call returned.")
        print("Response:", response.text)


if __name__ == "__main__":
    benchmark_tool_calling()