"""Tests for the pure possession-percentage calculation."""

from decimal import Decimal

from app.domain.possession import compute_possession_split


def test_returns_none_percentages_when_no_time_has_been_tracked() -> None:
    split = compute_possession_split(Decimal("0"), Decimal("0"))

    assert split.team_pct is None
    assert split.opponent_pct is None


def test_splits_possession_evenly() -> None:
    split = compute_possession_split(Decimal("300"), Decimal("300"))

    assert split.team_pct == 50.0
    assert split.opponent_pct == 50.0


def test_computes_an_uneven_split() -> None:
    split = compute_possession_split(Decimal("720"), Decimal("480"))

    assert split.team_pct == 60.0
    assert split.opponent_pct == 40.0


def test_percentages_always_sum_to_exactly_100() -> None:
    # opponent_pct is derived as 100 - team_pct (never rounded
    # independently), so this holds for any input by construction —
    # this test documents that invariant rather than hunting for a
    # specific pair of numbers that could break it.
    split = compute_possession_split(Decimal("511"), Decimal("489"))

    assert split.team_pct is not None
    assert split.opponent_pct is not None
    assert split.team_pct + split.opponent_pct == 100.0


def test_gives_full_possession_to_the_team_with_no_opponent_time_tracked() -> None:
    split = compute_possession_split(Decimal("600"), Decimal("0"))

    assert split.team_pct == 100.0
    assert split.opponent_pct == 0.0


def test_gives_full_possession_to_the_opponent_with_no_team_time_tracked() -> None:
    split = compute_possession_split(Decimal("0"), Decimal("600"))

    assert split.team_pct == 0.0
    assert split.opponent_pct == 100.0


def test_preserves_the_raw_seconds_unchanged() -> None:
    split = compute_possession_split(Decimal("123.45"), Decimal("67.89"))

    assert split.team_seconds == Decimal("123.45")
    assert split.opponent_seconds == Decimal("67.89")
