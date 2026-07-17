"""Tests for the event catalog: mirrors the test cases in the frontend's
`eventCatalog.test.ts`, so both sides are verified against the same rules.
"""

from app.domain.event_catalog import EVENT_TYPE_RULES, get_event_type_rules
from app.models.enums import EventType


def test_every_event_type_has_rules_defined() -> None:
    for event_type in EventType:
        assert event_type in EVENT_TYPE_RULES


def test_every_event_type_has_at_least_one_valid_result() -> None:
    for rules in EVENT_TYPE_RULES.values():
        assert len(rules.valid_results) > 0


def test_marks_all_pass_like_types_as_requiring_a_destination() -> None:
    for event_type in (
        EventType.SHORT_PASS,
        EventType.LONG_PASS,
        EventType.CROSS,
        EventType.THROUGH_BALL,
    ):
        assert get_event_type_rules(event_type).requires_destination is True


def test_marks_duels_as_not_requiring_a_destination() -> None:
    for event_type in (EventType.DRIBBLE_DUEL, EventType.TACKLE_DUEL, EventType.AERIAL_DUEL):
        assert get_event_type_rules(event_type).requires_destination is False


def test_marks_shots_as_requiring_a_body_part_but_not_a_destination() -> None:
    rules = get_event_type_rules(EventType.SHOT_OPEN_PLAY)

    assert rules.requires_destination is False
    assert rules.requires_body_part is True


def test_splits_set_pieces_between_pass_like_and_shot_like_destination_behavior() -> None:
    assert get_event_type_rules(EventType.CORNER_KICK).requires_destination is True
    assert get_event_type_rules(EventType.THROW_IN).requires_destination is True
    assert get_event_type_rules(EventType.DIRECT_FREE_KICK).requires_destination is False
    assert get_event_type_rules(EventType.DIRECT_FREE_KICK).requires_body_part is True
    assert get_event_type_rules(EventType.PENALTY_KICK).requires_body_part is True


def test_only_allows_the_pressure_tag_on_pass_like_events() -> None:
    assert get_event_type_rules(EventType.SHORT_PASS).allows_pressure is True
    assert get_event_type_rules(EventType.DRIBBLE_DUEL).allows_pressure is False
    assert get_event_type_rules(EventType.SHOT_OPEN_PLAY).allows_pressure is False
