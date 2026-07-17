"""Match model: a recorded game for a team, tied to its video and review status."""

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import MatchStatus

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.team import Team

_match_status_type = SAEnum(
    MatchStatus,
    name="match_status",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class Match(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "matches"

    team_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("teams.id"), nullable=False)
    opponent_name: Mapped[str | None] = mapped_column(default=None)
    match_date: Mapped[date | None] = mapped_column(default=None)
    video_url: Mapped[str | None] = mapped_column(default=None)
    video_duration_seconds: Mapped[int | None] = mapped_column(default=None)
    status: Mapped[MatchStatus] = mapped_column(
        _match_status_type, nullable=False, default=MatchStatus.IN_PROGRESS
    )

    team: Mapped["Team"] = relationship()
    events: Mapped[list["Event"]] = relationship(back_populates="match")

    def __repr__(self) -> str:
        return (
            f"Match(id={self.id!r}, opponent_name={self.opponent_name!r}, status={self.status!r})"
        )
