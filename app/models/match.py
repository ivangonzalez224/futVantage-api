"""Match model: a recorded game for a team, tied to its video and review status."""

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AttackDirection, MatchStatus

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.match_possession import MatchPossession
    from app.models.team import Team

_match_status_type = SAEnum(
    MatchStatus,
    name="match_status",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)

_attack_direction_type = SAEnum(
    AttackDirection,
    name="attack_direction",
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

    # Which way the tracked team attacks in the first half. The second
    # half is always the opposite (a rule of football — teams swap
    # ends at halftime), so we only need to store this once per match;
    # the frontend derives the second-half direction by flipping it.
    attacking_direction_first_half: Mapped[AttackDirection] = mapped_column(
        _attack_direction_type, nullable=False, default=AttackDirection.LEFT_TO_RIGHT
    )

    # Once true, the possession control on /annotate becomes read-only
    # — lets an analyst do a dedicated possession-tracking pass through
    # the video, then "seal" it before switching to a separate pass for
    # event annotation, without accidentally nudging the numbers.
    possession_tracking_locked: Mapped[bool] = mapped_column(nullable=False, default=False)

    team: Mapped["Team"] = relationship()
    events: Mapped[list["Event"]] = relationship(back_populates="match")
    possession_records: Mapped[list["MatchPossession"]] = relationship(
        back_populates="match", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"Match(id={self.id!r}, opponent_name={self.opponent_name!r}, status={self.status!r})"
        )
