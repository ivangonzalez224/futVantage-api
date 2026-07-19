"""Pure computation of individual player performance stats from a flat
list of events. Kept independent of the database and of `EventCategory`
so the math is trivial to unit test, and so set-piece events (which
carry the `set_piece` category but behave like a pass or a shot
depending on their `result`) are bucketed correctly automatically —
matching the architecture's rule that set pieces "inherit the logic of
passes or shots depending on the nature of the play".
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from app.models.enums import EventResult, PressureState


class EventLike(Protocol):
    """The minimal shape this module needs from an event.

    Deliberately just `result` and `pressure` — bucketing by which
    *family* of results a `result` belongs to (see `_PASS_FAMILY_RESULTS`
    etc. below) makes `category` unnecessary and handles set-piece
    events for free.
    """

    result: EventResult
    pressure: PressureState | None


def _pct(successful: int, total: int) -> float | None:
    if total == 0:
        return None
    return round(100 * successful / total, 1)


@dataclass(frozen=True)
class PassStats:
    total: int
    completed: int

    @property
    def completion_pct(self) -> float | None:
        return _pct(self.completed, self.total)


@dataclass(frozen=True)
class DuelStats:
    total: int
    won: int

    @property
    def win_pct(self) -> float | None:
        return _pct(self.won, self.total)


@dataclass(frozen=True)
class ShotStats:
    total: int
    goals: int
    on_target: int

    @property
    def conversion_pct(self) -> float | None:
        return _pct(self.goals, self.total)

    @property
    def accuracy_pct(self) -> float | None:
        return _pct(self.on_target, self.total)


@dataclass(frozen=True)
class DefensiveStats:
    total: int
    possession_retained: int

    @property
    def retention_pct(self) -> float | None:
        return _pct(self.possession_retained, self.total)


@dataclass(frozen=True)
class PressureStats:
    total_under_pressure: int
    successful_under_pressure: int

    @property
    def success_pct(self) -> float | None:
        return _pct(self.successful_under_pressure, self.total_under_pressure)


@dataclass(frozen=True)
class PlayerStats:
    passes: PassStats
    duels: DuelStats
    shots: ShotStats
    defensive_actions: DefensiveStats
    pressure: PressureStats


_PASS_FAMILY_RESULTS = {
    EventResult.COMPLETED,
    EventResult.INTERCEPTED,
    EventResult.OUT_OF_BOUNDS,
    EventResult.BLOCKED,
}
_DUEL_FAMILY_RESULTS = {
    EventResult.WON,
    EventResult.LOST,
    EventResult.FOUL_COMMITTED,
    EventResult.FOUL_RECEIVED,
}
_SHOT_FAMILY_RESULTS = {
    EventResult.GOAL,
    EventResult.SAVED,
    EventResult.OFF_TARGET,
    EventResult.POST_OR_CROSSBAR,
    EventResult.BLOCKED_DEFENDER,
}
_SHOT_ON_TARGET_RESULTS = {EventResult.GOAL, EventResult.SAVED}
_DEFENSIVE_FAMILY_RESULTS = {
    EventResult.POSSESSION_RETAINED,
    EventResult.POSSESSION_LOST,
    EventResult.TO_CORNER_OR_THROW,
}
_GENERAL_SUCCESS_RESULTS = {
    EventResult.COMPLETED,
    EventResult.WON,
    EventResult.GOAL,
    EventResult.POSSESSION_RETAINED,
}


def compute_player_stats(events: Sequence[EventLike]) -> PlayerStats:
    """Aggregates a flat list of events into per-category performance stats."""
    pass_total = pass_completed = 0
    duel_total = duel_won = 0
    shot_total = shot_goals = shot_on_target = 0
    defensive_total = defensive_retained = 0
    pressure_total = pressure_successful = 0

    for event in events:
        if event.result in _PASS_FAMILY_RESULTS:
            pass_total += 1
            if event.result == EventResult.COMPLETED:
                pass_completed += 1
        elif event.result in _DUEL_FAMILY_RESULTS:
            duel_total += 1
            if event.result == EventResult.WON:
                duel_won += 1
        elif event.result in _SHOT_FAMILY_RESULTS:
            shot_total += 1
            if event.result == EventResult.GOAL:
                shot_goals += 1
            if event.result in _SHOT_ON_TARGET_RESULTS:
                shot_on_target += 1
        elif event.result in _DEFENSIVE_FAMILY_RESULTS:
            defensive_total += 1
            if event.result == EventResult.POSSESSION_RETAINED:
                defensive_retained += 1

        if event.pressure == PressureState.UNDER_PRESSURE:
            pressure_total += 1
            if event.result in _GENERAL_SUCCESS_RESULTS:
                pressure_successful += 1

    return PlayerStats(
        passes=PassStats(total=pass_total, completed=pass_completed),
        duels=DuelStats(total=duel_total, won=duel_won),
        shots=ShotStats(total=shot_total, goals=shot_goals, on_target=shot_on_target),
        defensive_actions=DefensiveStats(
            total=defensive_total, possession_retained=defensive_retained
        ),
        pressure=PressureStats(
            total_under_pressure=pressure_total, successful_under_pressure=pressure_successful
        ),
    )
