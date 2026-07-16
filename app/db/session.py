"""Database engine, session factory, and the FastAPI dependency that hands
a request-scoped session to route handlers.
"""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def create_db_engine() -> Engine:
    """Creates the SQLAlchemy engine from the configured DATABASE_URL.

    Raises a clear error at call time (not at import time) if the URL is
    missing, so the app can still be imported/tested without a database
    configured (e.g. the health check endpoint doesn't need one).
    """
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set it in your environment or .env file."
        )
    return create_engine(settings.database_url, pool_pre_ping=True)


SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session, closed after the request."""
    session = SessionLocal(bind=create_db_engine())
    try:
        yield session
    finally:
        session.close()
