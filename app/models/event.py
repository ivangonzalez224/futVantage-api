"""Event model: a single annotated action (pass, duel, shot, etc.) tied to
a match, a team and a player, with its court coordinates and video
timestamp.
"""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    BodyPart,
    EventCategory,
    EventResult,
    EventType,
    MatchHalf,
    PressureState,
)

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.player import Player
    from app.models.team import Team


def _enum_type(enum_cls: type, name: str) -> SAEnum:
    """Builds a SQLAlchemy Enum column type from a Python str Enum.

    `values_callable` makes SQLAlchemy store the enum's *value*
    (e.g. "short_pass") instead of its member name (e.g. "SHORT_PASS"),
    matching what the frontend and the Pydantic schemas send.
    """
    return SAEnum(enum_cls, name=name, values_callable=lambda cls: [member.value for member in cls])


class Event(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "events"

    match_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("matches.id"), nullable=False)
    team_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("teams.id"), nullable=False)
    player_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("players.id"), nullable=False)

    category: Mapped[EventCategory] = mapped_column(
        _enum_type(EventCategory, "event_category"), nullable=False
    )
    type: Mapped[EventType] = mapped_column(_enum_type(EventType, "event_type"), nullable=False)
    result: Mapped[EventResult] = mapped_column(
        _enum_type(EventResult, "event_result"), nullable=False
    )

    # Normalized 0-100 coordinates (see the frontend's `coordinates.ts`);
    # independent of the analyst's screen resolution. By the time these
    # reach the backend, the frontend has already normalized `x_start`/
    # `x_end` so the tracked team always attacks toward x=100, regardless
    # of which side of the pitch they were actually on for this `half` —
    # see `app.domain.event_catalog` and the frontend's
    # `normalizeAttackingX` for the flip logic.
    x_start: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    y_start: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    x_end: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=None)
    y_end: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=None)

    video_timestamp_seconds: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)

    half: Mapped[MatchHalf] = mapped_column(_enum_type(MatchHalf, "match_half"), nullable=False)

    pressure: Mapped[PressureState | None] = mapped_column(
        _enum_type(PressureState, "pressure_state"), default=None
    )
    body_part: Mapped[BodyPart | None] = mapped_column(
        _enum_type(BodyPart, "body_part"), default=None
    )

    match: Mapped["Match"] = relationship(back_populates="events")
    team: Mapped["Team"] = relationship()
    player: Mapped["Player"] = relationship()

    def __repr__(self) -> str:
        return f"Event(id={self.id!r}, type={self.type!r}, result={self.result!r})"
