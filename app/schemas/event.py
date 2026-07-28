"""Pydantic schemas for the events API: request validation and response shape.

`EventCreate` re-validates every incoming event against the event
catalog (`app.domain.event_catalog`) — the same rules the frontend uses
to drive its UI — because the frontend's restrictions are a UX
convenience, not a security boundary. The backend is the last line of
defense against malformed or manually-crafted requests.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.event_catalog import get_event_type_rules
from app.models.enums import (
    BodyPart,
    EventCategory,
    EventResult,
    EventType,
    MatchHalf,
    PressureState,
)

_COORDINATE_RANGE = Field(ge=Decimal("0"), le=Decimal("100"))


class EventCreate(BaseModel):
    team_id: UUID
    player_id: UUID
    type: EventType
    result: EventResult
    x_start: Decimal = _COORDINATE_RANGE
    y_start: Decimal = _COORDINATE_RANGE
    x_end: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("100"))
    y_end: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("100"))
    video_timestamp_seconds: Decimal = Field(ge=Decimal("0"))
    half: MatchHalf
    pressure: PressureState | None = None
    body_part: BodyPart | None = None

    @model_validator(mode="after")
    def validate_against_catalog(self) -> "EventCreate":
        rules = get_event_type_rules(self.type)

        if self.result not in rules.valid_results:
            raise ValueError(
                f"Result '{self.result.value}' is not valid for event type '{self.type.value}'."
            )

        has_destination = self.x_end is not None or self.y_end is not None
        if rules.requires_destination and not has_destination:
            raise ValueError(
                f"Event type '{self.type.value}' requires a destination (x_end and y_end)."
            )
        if not rules.requires_destination and has_destination:
            raise ValueError(f"Event type '{self.type.value}' does not accept a destination.")

        if rules.requires_body_part and self.body_part is None:
            raise ValueError(f"Event type '{self.type.value}' requires a body_part.")

        if not rules.allows_pressure and self.pressure is not None:
            raise ValueError(f"Event type '{self.type.value}' does not accept the pressure tag.")

        return self


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    match_id: UUID
    team_id: UUID
    player_id: UUID
    category: EventCategory
    type: EventType
    result: EventResult
    x_start: Decimal
    y_start: Decimal
    x_end: Decimal | None
    y_end: Decimal | None
    video_timestamp_seconds: Decimal
    half: MatchHalf
    pressure: PressureState | None
    body_part: BodyPart | None
    created_at: datetime
