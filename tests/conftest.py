"""Shared pytest fixtures for database-backed tests."""

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session, SessionTransaction
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

    The two event listeners below are SQLAlchemy's own documented
    workaround for a long-standing bug in Python's built-in `sqlite3`
    driver: by default it silently manages its own transactions behind
    SQLAlchemy's back, which breaks SAVEPOINT-based test isolation (see
    `db_session` below) — every commit inside a test would otherwise
    leak into the next one. See "Serializable isolation / Savepoints"
    in SQLAlchemy's SQLite dialect docs for the full explanation.
    """
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(test_engine, "connect")
    def _disable_pysqlite_own_transaction_handling(
        dbapi_connection: Any, _connection_record: Any
    ) -> None:
        dbapi_connection.isolation_level = None

    @event.listens_for(test_engine, "begin")
    def _emit_our_own_begin(connection: Connection) -> None:
        connection.exec_driver_sql("BEGIN")

    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def db_session(engine: Engine) -> Generator[Session, None, None]:
    """A database session wrapped in a transaction that's rolled back after
    each test, so tests never leak state into one another.

    Uses SQLAlchemy's documented pattern for nesting a test's work inside
    an external transaction: `join_transaction_mode="create_savepoint"`
    makes the session operate through a SAVEPOINT instead of the outer
    transaction directly, and the `after_transaction_end` event restarts
    a new SAVEPOINT every time one ends (e.g. after `session.commit()`),
    so any number of commits inside a test — including ones triggered
    indirectly through the API via the `client` fixture — stay nested
    inside the outer transaction we roll back at teardown.

    This alone is NOT sufficient on SQLite without the engine-level
    workaround in the `engine` fixture above; without it, SAVEPOINTs
    silently fail to nest and every commit becomes permanent, leaking
    across tests. We found this the hard way: a `POST /matches` call in
    one test was still visible in a completely unrelated later test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(session: Session, transaction_ended: SessionTransaction) -> None:
        if transaction_ended.nested and not transaction_ended._parent.nested:  # type: ignore[union-attr]
            session.begin_nested()

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
