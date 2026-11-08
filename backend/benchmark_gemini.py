"""
Benchmark an alternative Gemini model independently.
"""
import time
from app.services.gemini_service import get_gemini_client

MODEL = "gemini-3.5-flash-lite"

def benchmark_text_response():
    client = get_gemini_client()

    print(f"\nBenchmarking model: {MODEL}")

    start = time.perf_counter()

    response = client.models.generate_content(
        model=MODEL,
        contents="Reply in one short sentence: What is a monthly budget?",
    )

    elapsed = time.perf_counter() - start

    print(f"\nResponse: {response.text}")
    print(f"Latency: {elapsed:.2f} seconds")


if __name__ == "__main__":
    benchmark_text_response()