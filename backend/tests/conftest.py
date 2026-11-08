from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine, get_db
from app.main import app


@pytest.fixture(scope="session")
def test_database_schema() -> Generator[None, None, None]:
    """
    Create an isolated schema for API integration tests.

    This fixture is intentionally not autouse: ordinary unit tests should
    run with the application's normal development defaults.
    """
    settings = get_settings()

    if settings.environment != "testing":
        raise RuntimeError(
            "API integration tests require ENVIRONMENT=testing. "
            "Use a dedicated test database; never point tests at development "
            "or production data."
        )

    if engine.dialect.name != "postgresql":
        raise RuntimeError(
            "API integration tests require PostgreSQL because the application "
            "uses PostgreSQL-specific database constraints."
        )

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client(
    test_database_schema: None,
) -> Generator[TestClient, None, None]:
    """
    Give each integration test an outer database transaction.

    Application services may call commit(); SQLAlchemy's
    create_savepoint mode keeps those commits inside the outer transaction,
    allowing the complete test to roll back without leaking test data.
    """
    connection = engine.connect()
    outer_transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
        join_transaction_mode="create_savepoint",
    )

    def override_get_db() -> Generator[Session, None, None]:
        with TestingSessionLocal() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        outer_transaction.rollback()
        connection.close()
