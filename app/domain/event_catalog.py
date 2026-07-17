"""Event catalog: the validation rules for each event type.

This is the Python counterpart of the frontend's `eventCatalog.ts`
(in `tactical-scout-web`). Both must stay in sync: the frontend uses its
copy to drive the annotation UI (which fields to show/require), and the
backend uses this one as the source of truth to *validate* incoming
events, since the frontend's UI restrictions alone can't be trusted.
"""

from dataclasses import dataclass

from app.models.enums import EventCategory, EventResult, EventType


@dataclass(frozen=True)
class EventTypeRules:
    category: EventCategory
    requires_destination: bool
    allows_pressure: bool
    requires_body_part: bool
    valid_results: frozenset[EventResult]


_PASS_RESULTS = frozenset(
    {
        EventResult.COMPLETED,
        EventResult.INTERCEPTED,
        EventResult.OUT_OF_BOUNDS,
        EventResult.BLOCKED,
    }
)

_DUEL_RESULTS = frozenset(
    {
        EventResult.WON,
        EventResult.LOST,
        EventResult.FOUL_COMMITTED,
        EventResult.FOUL_RECEIVED,
    }
)

_SHOT_RESULTS = frozenset(
    {
        EventResult.GOAL,
        EventResult.SAVED,
        EventResult.OFF_TARGET,
        EventResult.POST_OR_CROSSBAR,
        EventResult.BLOCKED_DEFENDER,
    }
)

_DEFENSIVE_RESULTS = frozenset(
    {
        EventResult.POSSESSION_RETAINED,
        EventResult.POSSESSION_LOST,
        EventResult.TO_CORNER_OR_THROW,
    }
)

EVENT_TYPE_RULES: dict[EventType, EventTypeRules] = {
    EventType.SHORT_PASS: EventTypeRules(EventCategory.PASS, True, True, False, _PASS_RESULTS),
    EventType.LONG_PASS: EventTypeRules(EventCategory.PASS, True, True, False, _PASS_RESULTS),
    EventType.CROSS: EventTypeRules(EventCategory.PASS, True, True, False, _PASS_RESULTS),
    EventType.THROUGH_BALL: EventTypeRules(EventCategory.PASS, True, True, False, _PASS_RESULTS),
    EventType.DRIBBLE_DUEL: EventTypeRules(EventCategory.DUEL, False, False, False, _DUEL_RESULTS),
    EventType.TACKLE_DUEL: EventTypeRules(EventCategory.DUEL, False, False, False, _DUEL_RESULTS),
    EventType.AERIAL_DUEL: EventTypeRules(EventCategory.DUEL, False, False, False, _DUEL_RESULTS),
    EventType.SHOT_OPEN_PLAY: EventTypeRules(EventCategory.SHOT, False, False, True, _SHOT_RESULTS),
    EventType.HEADER_SHOT: EventTypeRules(EventCategory.SHOT, False, False, True, _SHOT_RESULTS),
    EventType.CORNER_KICK: EventTypeRules(
        EventCategory.SET_PIECE, True, False, False, _PASS_RESULTS
    ),
    EventType.DIRECT_FREE_KICK: EventTypeRules(
        EventCategory.SET_PIECE, False, False, True, _SHOT_RESULTS
    ),
    EventType.INDIRECT_FREE_KICK: EventTypeRules(
        EventCategory.SET_PIECE, True, False, False, _PASS_RESULTS
    ),
    EventType.PENALTY_KICK: EventTypeRules(
        EventCategory.SET_PIECE, False, False, True, _SHOT_RESULTS
    ),
    EventType.THROW_IN: EventTypeRules(EventCategory.SET_PIECE, True, False, False, _PASS_RESULTS),
    EventType.INTERCEPTION: EventTypeRules(
        EventCategory.DEFENSIVE_ACTION, False, False, False, _DEFENSIVE_RESULTS
    ),
    EventType.CLEARANCE: EventTypeRules(
        EventCategory.DEFENSIVE_ACTION, False, False, False, _DEFENSIVE_RESULTS
    ),
    EventType.LOOSE_BALL_RECOVERY: EventTypeRules(
        EventCategory.DEFENSIVE_ACTION, False, False, False, _DEFENSIVE_RESULTS
    ),
    EventType.GOALKEEPER_SAVE: EventTypeRules(
        EventCategory.DEFENSIVE_ACTION, False, False, False, _DEFENSIVE_RESULTS
    ),
}


def get_event_type_rules(event_type: EventType) -> EventTypeRules:
    """Returns the validation rules for a given event type.

    Every `EventType` member is guaranteed to have an entry in
    `EVENT_TYPE_RULES` (enforced by a unit test), so this never raises
    for a valid `EventType` value.
    """
    return EVENT_TYPE_RULES[event_type]
