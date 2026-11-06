from fastapi import FastAPI

from app.core.config import get_settings
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.accounts import router as accounts_router
from app.api.v1.endpoints.transactions import router as transactions_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Personal Finance Management Platform",
)

# Register authentication endpoints.
app.include_router(
    auth_router,
    prefix=settings.api_v1_prefix,
)

# Register user endpoints.
app.include_router(
    users_router,
    prefix=settings.api_v1_prefix,
)


# Register financial account endpoints.
app.include_router(
    accounts_router,
    prefix=settings.api_v1_prefix,
)


app.include_router(
    transactions_router,
    prefix=f"{settings.api_v1_prefix}/transactions",
    tags=["Transactions"],
)


# Health-check endpoint.
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