"""Tests for the EventCreate schema's catalog-based validation."""

from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.event import EventCreate

_TEAM_ID = uuid4()
_PLAYER_ID = uuid4()


def _base_payload(**overrides: object) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "team_id": _TEAM_ID,
        "player_id": _PLAYER_ID,
        "type": "tackle_duel",
        "result": "won",
        "x_start": Decimal("30.00"),
        "y_start": Decimal("40.00"),
        "video_timestamp_seconds": Decimal("612.00"),
        "half": "first_half",
    }
    payload.update(overrides)
    return payload


def test_accepts_a_valid_event_with_no_destination() -> None:
    event = EventCreate(**_base_payload())

    assert event.type.value == "tackle_duel"
    assert event.x_end is None
    assert event.half.value == "first_half"


def test_accepts_a_pass_like_event_with_destination_and_pressure() -> None:
    event = EventCreate(
        **_base_payload(
            type="short_pass",
            result="completed",
            x_end=Decimal("60.00"),
            y_end=Decimal("55.00"),
            pressure="under_pressure",
        )
    )

    assert event.x_end == Decimal("60.00")
    assert event.pressure is not None
    assert event.pressure.value == "under_pressure"


def test_rejects_a_pass_like_event_missing_the_destination() -> None:
    with pytest.raises(ValidationError, match="requires a destination"):
        EventCreate(**_base_payload(type="short_pass", result="completed"))


def test_rejects_a_destination_for_a_type_that_does_not_accept_one() -> None:
    with pytest.raises(ValidationError, match="does not accept a destination"):
        EventCreate(
            **_base_payload(
                type="tackle_duel", result="won", x_end=Decimal("60.00"), y_end=Decimal("55.00")
            )
        )


def test_rejects_a_result_not_valid_for_the_event_type() -> None:
    with pytest.raises(ValidationError, match="is not valid for event type"):
        EventCreate(**_base_payload(type="tackle_duel", result="goal"))


def test_rejects_a_shot_missing_the_body_part() -> None:
    with pytest.raises(ValidationError, match="requires a body_part"):
        EventCreate(**_base_payload(type="shot_open_play", result="goal"))


def test_accepts_a_shot_with_the_body_part() -> None:
    event = EventCreate(
        **_base_payload(type="shot_open_play", result="goal", body_part="right_foot")
    )

    assert event.body_part is not None
    assert event.body_part.value == "right_foot"


def test_rejects_pressure_tag_on_a_type_that_does_not_allow_it() -> None:
    with pytest.raises(ValidationError, match="does not accept the pressure tag"):
        EventCreate(**_base_payload(type="tackle_duel", result="won", pressure="no_pressure"))


def test_rejects_coordinates_outside_the_0_to_100_range() -> None:
    with pytest.raises(ValidationError):
        EventCreate(**_base_payload(x_start=Decimal("150.00")))


def test_rejects_a_missing_half() -> None:
    payload = _base_payload()
    del payload["half"]

    with pytest.raises(ValidationError):
        EventCreate(**payload)
