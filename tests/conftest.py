"""Shared pytest fixtures for database-backed tests."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - registers all models with Base.metadata
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    """A SQLite in-memory engine, shared for the whole test session.

    SQLite is used here instead of Postgres to keep the test suite fast
    and dependency-free (no database server required to run `pytest`).
    The ORM layer doesn't use any Postgres-specific types yet, so this
    gives equivalent coverage for now; if we introduce Postgres-only
    features (native ENUM, JSONB, etc.) we'll add a Postgres-backed test
    tier alongside this one, likely via a GitHub Actions service
    container in CI.
    """
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def db_session(engine: Engine) -> Generator[Session, None, None]:
    """A database session wrapped in a transaction that's rolled back after
    each test, so tests never leak state into one another.

    Uses `join_transaction_mode="create_savepoint"` so that a test which
    calls `session.commit()` (including one that fails with an
    IntegrityError) still gets cleanly rolled back afterward, instead of
    leaving the outer transaction in a deassociated state.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """A FastAPI TestClient whose `get_db` dependency is overridden to
    reuse the same transactional `db_session`, so API tests see (and
    clean up) the exact same data as a direct-to-ORM test would.
    """

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(fastapi_app)
    finally:
        fastapi_app.dependency_overrides.clear()
