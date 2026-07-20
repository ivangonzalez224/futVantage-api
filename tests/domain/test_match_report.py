"""Tests for the pure match report computation."""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.match_report import compute_match_report
from app.models.enums import EventResult, EventType, PressureState


@dataclass
class FakeMatchEvent:
    """A minimal stand-in for an Event, satisfying `MatchEventLike` without touching the DB."""

    type: EventType
    result: EventResult
    x_start: Decimal
    y_start: Decimal
    pressure: PressureState | None = None


def test_computes_team_totals_from_all_events() -> None:
    events = [
        FakeMatchEvent(EventType.SHORT_PASS, EventResult.COMPLETED, Decimal("50"), Decimal("50")),
        FakeMatchEvent(EventType.SHORT_PASS, EventResult.INTERCEPTED, Decimal("50"), Decimal("50")),
        FakeMatchEvent(EventType.TACKLE_DUEL, EventResult.WON, Decimal("30"), Decimal("50")),
    ]

    report = compute_match_report(events)

    assert report.team_totals.passes.total == 2
    assert report.team_totals.passes.completed == 1
    assert report.team_totals.duels.won == 1


def test_computes_set_piece_effectiveness_across_pass_like_and_shot_like_types() -> None:
    events = [
        FakeMatchEvent(EventType.CORNER_KICK, EventResult.COMPLETED, Decimal("95"), Decimal("50")),
        FakeMatchEvent(
            EventType.CORNER_KICK, EventResult.OUT_OF_BOUNDS, Decimal("95"), Decimal("50")
        ),
        FakeMatchEvent(EventType.PENALTY_KICK, EventResult.GOAL, Decimal("89"), Decimal("50")),
        # Not a set piece: should not count towards set_pieces at all.
        FakeMatchEvent(EventType.SHORT_PASS, EventResult.COMPLETED, Decimal("50"), Decimal("50")),
    ]

    report = compute_match_report(events)

    assert report.set_pieces.total == 3
    assert report.set_pieces.successful == 2  # completed + goal count, out_of_bounds doesn't
    assert report.set_pieces.effectiveness_pct == 66.7


def test_returns_none_effectiveness_when_no_set_pieces_occurred() -> None:
    events = [
        FakeMatchEvent(EventType.SHORT_PASS, EventResult.COMPLETED, Decimal("50"), Decimal("50"))
    ]

    report = compute_match_report(events)

    assert report.set_pieces.total == 0
    assert report.set_pieces.effectiveness_pct is None


def test_buckets_attack_flow_by_lateral_band() -> None:
    events = [
        FakeMatchEvent(
            EventType.SHORT_PASS, EventResult.COMPLETED, Decimal("50"), Decimal("10")
        ),  # left
        FakeMatchEvent(
            EventType.SHORT_PASS, EventResult.COMPLETED, Decimal("50"), Decimal("50")
        ),  # center
        FakeMatchEvent(
            EventType.SHORT_PASS, EventResult.COMPLETED, Decimal("50"), Decimal("90")
        ),  # right
        FakeMatchEvent(
            EventType.SHORT_PASS, EventResult.COMPLETED, Decimal("50"), Decimal("33.33")
        ),  # left (boundary)
        FakeMatchEvent(
            EventType.SHORT_PASS, EventResult.COMPLETED, Decimal("50"), Decimal("66.67")
        ),  # right (boundary)
    ]

    report = compute_match_report(events)

    assert report.attack_flow.left_band == 2
    assert report.attack_flow.center == 1
    assert report.attack_flow.right_band == 2
    assert report.attack_flow.total == 5


def test_collects_possession_loss_zones_with_pressure_flag() -> None:
    events = [
        FakeMatchEvent(
            EventType.SHORT_PASS,
            EventResult.INTERCEPTED,
            Decimal("40"),
            Decimal("60"),
            pressure=PressureState.UNDER_PRESSURE,
        ),
        FakeMatchEvent(
            EventType.TACKLE_DUEL,
            EventResult.LOST,
            Decimal("20"),
            Decimal("30"),
        ),
        # A completed pass is not a loss, so it should be excluded.
        FakeMatchEvent(EventType.SHORT_PASS, EventResult.COMPLETED, Decimal("50"), Decimal("50")),
    ]

    report = compute_match_report(events)

    assert len(report.possession_loss_zones) == 2
    assert report.possession_loss_zones[0].x == Decimal("40")
    assert report.possession_loss_zones[0].under_pressure is True
    assert report.possession_loss_zones[1].under_pressure is False


def test_empty_match_returns_zeroed_report() -> None:
    report = compute_match_report([])

    assert report.team_totals.passes.total == 0
    assert report.set_pieces.total == 0
    assert report.attack_flow.total == 0
    assert report.possession_loss_zones == []
