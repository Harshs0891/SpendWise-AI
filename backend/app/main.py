from fastapi import FastAPI

app = FastAPI(
    title="SpendWise AI",
    description="Personal Finance Management Platform",
    version="0.1.0",
)


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "application": "SpendWise AI",
    }