"""Pure computation of team-level match report data: set-piece
effectiveness, attack flow by band (left/center/right), and
possession-loss zones for a heatmap.

Reuses `compute_player_stats` for the team-wide totals (pass %, duel %,
shot conversion, defensive retention, pressure success), since the
category/result bucketing logic is identical whether you're summarizing
one player's events or the whole squad's.

NOTE on scope: the architecture also calls for a visual pass network
between players. That isn't computable yet — the `events` table stores
a pass's destination *coordinate* but not the *receiving player*, so
there's no player-to-player data to build a network from without
guessing. Adding a `target_player_id` column to `Event` would unlock
this in a future iteration; it's intentionally left out here rather
than faked.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from app.domain.player_stats import EventLike, PlayerStats, compute_player_stats
from app.models.enums import EventResult, EventType, PressureState


class MatchEventLike(EventLike, Protocol):
    """Everything this module needs from an event, layered on top of the
    smaller `EventLike` protocol `compute_player_stats` already uses.
    """

    type: EventType
    x_start: Decimal
    y_start: Decimal


_SET_PIECE_TYPES = {
    EventType.CORNER_KICK,
    EventType.DIRECT_FREE_KICK,
    EventType.INDIRECT_FREE_KICK,
    EventType.PENALTY_KICK,
    EventType.THROW_IN,
}

_LOSS_RESULTS = {
    EventResult.INTERCEPTED,
    EventResult.OUT_OF_BOUNDS,
    EventResult.BLOCKED,
    EventResult.LOST,
    EventResult.POSSESSION_LOST,
}

_SUCCESS_RESULTS = {
    EventResult.COMPLETED,
    EventResult.WON,
    EventResult.GOAL,
    EventResult.POSSESSION_RETAINED,
}

# The pitch width (y-axis, 0-100) is split into three equal bands.
_BAND_BOUNDARY_LOW = Decimal("33.34")
_BAND_BOUNDARY_HIGH = Decimal("66.67")


@dataclass(frozen=True)
class SetPieceStats:
    total: int
    successful: int

    @property
    def effectiveness_pct(self) -> float | None:
        if self.total == 0:
            return None
        return round(100 * self.successful / self.total, 1)


@dataclass(frozen=True)
class AttackFlow:
    left_band: int
    center: int
    right_band: int

    @property
    def total(self) -> int:
        return self.left_band + self.center + self.right_band


@dataclass(frozen=True)
class PossessionLossPoint:
    x: Decimal
    y: Decimal
    under_pressure: bool


@dataclass(frozen=True)
class MatchReport:
    team_totals: PlayerStats
    set_pieces: SetPieceStats
    attack_flow: AttackFlow
    possession_loss_zones: list[PossessionLossPoint]


def _band_for_y(y: Decimal) -> str:
    if y < _BAND_BOUNDARY_LOW:
        return "left"
    if y < _BAND_BOUNDARY_HIGH:
        return "center"
    return "right"


def compute_match_report(events: Sequence[MatchEventLike]) -> MatchReport:
    """Aggregates every event of a match into a team-level report."""
    team_totals = compute_player_stats(events)

    set_piece_total = set_piece_successful = 0
    left = center = right = 0
    loss_zones: list[PossessionLossPoint] = []

    for event in events:
        if event.type in _SET_PIECE_TYPES:
            set_piece_total += 1
            if event.result in _SUCCESS_RESULTS:
                set_piece_successful += 1

        band = _band_for_y(event.y_start)
        if band == "left":
            left += 1
        elif band == "center":
            center += 1
        else:
            right += 1

        if event.result in _LOSS_RESULTS:
            loss_zones.append(
                PossessionLossPoint(
                    x=event.x_start,
                    y=event.y_start,
                    under_pressure=event.pressure == PressureState.UNDER_PRESSURE,
                )
            )

    return MatchReport(
        team_totals=team_totals,
        set_pieces=SetPieceStats(total=set_piece_total, successful=set_piece_successful),
        attack_flow=AttackFlow(left_band=left, center=center, right_band=right),
        possession_loss_zones=loss_zones,
    )
