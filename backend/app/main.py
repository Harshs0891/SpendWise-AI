from fastapi import FastAPI

from app.core.config import get_settings

# Import the authentication router.
from app.api.v1.endpoints.auth import router as auth_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Personal Finance Management Platform",
)

# Register authentication endpoints under the configured API version prefix.
app.include_router(
    auth_router,
    prefix=settings.api_v1_prefix,
)


# Check whether the SpendWise AI backend is healthy.
@app.get(f"{settings.api_v1_prefix}/health")
def health_check():
    """
    Return the current application health status.
    """

    return {
        "status": "healthy",
        "application": settings.app_name,
        "environment": settings.environment,
    }