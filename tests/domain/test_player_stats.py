"""Tests for the pure player-stats computation."""

from dataclasses import dataclass

from app.domain.player_stats import compute_player_stats
from app.models.enums import EventResult, PressureState


@dataclass
class FakeEvent:
    """A minimal stand-in for an Event, satisfying `EventLike` without touching the DB."""

    result: EventResult
    pressure: PressureState | None = None


def test_computes_pass_completion_percentage() -> None:
    events = [
        FakeEvent(EventResult.COMPLETED),
        FakeEvent(EventResult.COMPLETED),
        FakeEvent(EventResult.COMPLETED),
        FakeEvent(EventResult.INTERCEPTED),
    ]

    stats = compute_player_stats(events)

    assert stats.passes.total == 4
    assert stats.passes.completed == 3
    assert stats.passes.completion_pct == 75.0


def test_computes_duel_win_percentage() -> None:
    events = [FakeEvent(EventResult.WON), FakeEvent(EventResult.LOST)]

    stats = compute_player_stats(events)

    assert stats.duels.total == 2
    assert stats.duels.won == 1
    assert stats.duels.win_pct == 50.0


def test_computes_shot_conversion_and_accuracy() -> None:
    events = [
        FakeEvent(EventResult.GOAL),
        FakeEvent(EventResult.SAVED),
        FakeEvent(EventResult.OFF_TARGET),
        FakeEvent(EventResult.OFF_TARGET),
    ]

    stats = compute_player_stats(events)

    assert stats.shots.total == 4
    assert stats.shots.goals == 1
    assert stats.shots.on_target == 2  # goal + saved
    assert stats.shots.conversion_pct == 25.0
    assert stats.shots.accuracy_pct == 50.0


def test_computes_defensive_retention_percentage() -> None:
    events = [
        FakeEvent(EventResult.POSSESSION_RETAINED),
        FakeEvent(EventResult.POSSESSION_RETAINED),
        FakeEvent(EventResult.POSSESSION_LOST),
        FakeEvent(EventResult.TO_CORNER_OR_THROW),
    ]

    stats = compute_player_stats(events)

    assert stats.defensive_actions.total == 4
    assert stats.defensive_actions.possession_retained == 2
    assert stats.defensive_actions.retention_pct == 50.0


def test_computes_success_rate_under_pressure_only() -> None:
    events = [
        FakeEvent(EventResult.COMPLETED, pressure=PressureState.UNDER_PRESSURE),
        FakeEvent(EventResult.INTERCEPTED, pressure=PressureState.UNDER_PRESSURE),
        FakeEvent(EventResult.COMPLETED, pressure=PressureState.NO_PRESSURE),  # excluded
        FakeEvent(EventResult.COMPLETED, pressure=None),  # excluded
    ]

    stats = compute_player_stats(events)

    assert stats.pressure.total_under_pressure == 2
    assert stats.pressure.successful_under_pressure == 1
    assert stats.pressure.success_pct == 50.0


def test_buckets_set_piece_events_by_result_family_not_category() -> None:
    # A corner kick (category=set_piece) uses pass-family results, and a
    # penalty kick (category=set_piece) uses shot-family results. Both
    # should be bucketed correctly using only `result`, per the
    # architecture's "set pieces inherit pass/shot logic" rule.
    events = [
        FakeEvent(EventResult.COMPLETED),  # corner kick, completed
        FakeEvent(EventResult.GOAL),  # penalty kick, scored
    ]

    stats = compute_player_stats(events)

    assert stats.passes.total == 1
    assert stats.passes.completed == 1
    assert stats.shots.total == 1
    assert stats.shots.goals == 1


def test_returns_none_percentages_when_a_category_has_no_events() -> None:
    stats = compute_player_stats([])

    assert stats.passes.completion_pct is None
    assert stats.duels.win_pct is None
    assert stats.shots.conversion_pct is None
    assert stats.shots.accuracy_pct is None
    assert stats.defensive_actions.retention_pct is None
    assert stats.pressure.success_pct is None
