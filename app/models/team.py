"""Team model: belongs to an academy, groups players by category (e.g. Sub-15)."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.academy import Academy
    from app.models.player import Player
    from app.models.user import User


class Team(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "teams"

    academy_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("academies.id"), nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    category: Mapped[str] = mapped_column(nullable=False)

    # Nullable on purpose: teams seeded before authentication existed have
    # no owner yet. `PATCH /teams/{id}/claim` lets a logged-in user adopt
    # one of these "orphan" teams instead of losing that data.
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True, default=None
    )

    academy: Mapped["Academy"] = relationship(back_populates="teams")
    players: Mapped[list["Player"]] = relationship(back_populates="team")
    owner: Mapped["User | None"] = relationship()

    def __repr__(self) -> str:
        return f"Team(id={self.id!r}, name={self.name!r}, category={self.category!r})"
