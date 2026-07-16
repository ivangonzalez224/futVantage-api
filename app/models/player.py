"""Player model: belongs to a team, uniquely identified within it by jersey number."""

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, SmallInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.team import Team


class Player(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "players"
    __table_args__ = (UniqueConstraint("team_id", "jersey_number", name="uq_player_team_jersey"),)

    team_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("teams.id"), nullable=False)
    jersey_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    full_name: Mapped[str] = mapped_column(nullable=False)
    position: Mapped[str | None] = mapped_column(default=None)
    birth_date: Mapped[date | None] = mapped_column(default=None)

    team: Mapped["Team"] = relationship(back_populates="players")

    def __repr__(self) -> str:
        return (
            f"Player(id={self.id!r}, jersey_number={self.jersey_number!r}, "
            f"full_name={self.full_name!r})"
        )
