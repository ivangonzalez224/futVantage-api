"""Declarative base and reusable mixins for SQLAlchemy models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import Uuid


class Base(DeclarativeBase):
    """Base class every ORM model inherits from."""


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key, generated in Python (portable across DB engines)."""

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    """Adds a `created_at` column set by the database at insert time."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
