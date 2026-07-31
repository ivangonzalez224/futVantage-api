"""MatchPossession model: accumulated ball-possession seconds for the
tracked team and its opponent, kept separately per half.

One row per (match, half) — see the unique constraint below. Seconds
are accumulated by the frontend as the video plays (see
`app.domain.possession` for the percentage calculation), not measured
by a server-side clock, since the source of truth for "how much time
passed" is the video's own timeline, not wall-clock time.
"""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import MatchHalf

if TYPE_CHECKING:
    from app.models.match import Match

# Reuses the "match_half" Postgres enum type already created by the
# events migration — `create_type=False` tells SQLAlchemy not to try
# creating it again (it would fail with "type already exists").
_match_half_type = SAEnum(
    MatchHalf,
    name="match_half",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
    create_type=False,
)


class MatchPossession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "match_possession"
    __table_args__ = (UniqueConstraint("match_id", "half", name="uq_match_possession_match_half"),)

    match_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("matches.id"), nullable=False)
    half: Mapped[MatchHalf] = mapped_column(_match_half_type, nullable=False)

    team_seconds: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), nullable=False, default=Decimal("0")
    )
    opponent_seconds: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), nullable=False, default=Decimal("0")
    )
    # Where the video was the last time this row was saved — powers the
    # "Continuar desde el minuto X" button on the frontend.
    last_video_timestamp_seconds: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2), default=None
    )

    match: Mapped["Match"] = relationship(back_populates="possession_records")

    def __repr__(self) -> str:
        return f"MatchPossession(match_id={self.match_id!r}, half={self.half!r})"
