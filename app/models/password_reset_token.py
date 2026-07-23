"""Password reset token model.

Stores only a hash of the raw token (the same idea as password
hashing): if the database ever leaked, a stolen row wouldn't let anyone
reset a password, since the raw token that was emailed to the user is
never persisted anywhere.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class PasswordResetToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "password_reset_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    # Explicitly timezone-aware, matching TimestampMixin.created_at — a
    # plain `Mapped[datetime]` defaults to a naive DateTime column, which
    # would raise `TypeError: can't compare offset-naive and
    # offset-aware datetimes` the moment this gets compared against
    # `datetime.now(UTC)` in the reset-password logic.
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"PasswordResetToken(id={self.id!r}, user_id={self.user_id!r})"
