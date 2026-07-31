"""Pydantic schemas for the match possession API."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MatchHalf


class PossessionHalfRead(BaseModel):
    """Possession for a single half, with percentages already computed
    (see `app.domain.possession`) — the frontend never divides, it just
    displays these numbers.
    """

    model_config = ConfigDict(from_attributes=True)

    half: MatchHalf
    team_seconds: Decimal
    opponent_seconds: Decimal
    team_pct: float | None
    opponent_pct: float | None
    last_video_timestamp_seconds: Decimal | None


class PossessionTotalsRead(BaseModel):
    """First half + second half combined."""

    team_seconds: Decimal
    opponent_seconds: Decimal
    team_pct: float | None
    opponent_pct: float | None


class PossessionRead(BaseModel):
    match_id: UUID
    tracking_locked: bool
    first_half: PossessionHalfRead
    second_half: PossessionHalfRead
    total: PossessionTotalsRead


class PossessionUpdateRequest(BaseModel):
    """Sent automatically by the frontend on every possession toggle and
    on every pause — not something the analyst fills in by hand.
    """

    half: MatchHalf
    team_seconds: Decimal = Field(ge=Decimal("0"))
    opponent_seconds: Decimal = Field(ge=Decimal("0"))
    last_video_timestamp_seconds: Decimal | None = Field(default=None, ge=Decimal("0"))


class PossessionResetRequest(BaseModel):
    half: MatchHalf


class PossessionLockRequest(BaseModel):
    locked: bool


class PossessionLockRead(BaseModel):
    tracking_locked: bool
