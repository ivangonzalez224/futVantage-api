"""Domain enums shared by the ORM models and the API schemas.

These mirror the `event_category` / `event_type` / `event_result` values
used in the frontend's event catalog (`tactical-scout-web`), so both
sides of the system speak the same vocabulary.
"""

import enum


class EventCategory(str, enum.Enum):
    PASS = "pass"
    DUEL = "duel"
    SHOT = "shot"
    SET_PIECE = "set_piece"
    DEFENSIVE_ACTION = "defensive_action"


class EventType(str, enum.Enum):
    SHORT_PASS = "short_pass"
    LONG_PASS = "long_pass"
    CROSS = "cross"
    THROUGH_BALL = "through_ball"
    DRIBBLE_DUEL = "dribble_duel"
    TACKLE_DUEL = "tackle_duel"
    AERIAL_DUEL = "aerial_duel"
    SHOT_OPEN_PLAY = "shot_open_play"
    HEADER_SHOT = "header_shot"
    CORNER_KICK = "corner_kick"
    DIRECT_FREE_KICK = "direct_free_kick"
    INDIRECT_FREE_KICK = "indirect_free_kick"
    PENALTY_KICK = "penalty_kick"
    THROW_IN = "throw_in"
    INTERCEPTION = "interception"
    CLEARANCE = "clearance"
    LOOSE_BALL_RECOVERY = "loose_ball_recovery"
    GOALKEEPER_SAVE = "goalkeeper_save"


class EventResult(str, enum.Enum):
    COMPLETED = "completed"
    INTERCEPTED = "intercepted"
    OUT_OF_BOUNDS = "out_of_bounds"
    BLOCKED = "blocked"
    WON = "won"
    LOST = "lost"
    FOUL_COMMITTED = "foul_committed"
    FOUL_RECEIVED = "foul_received"
    GOAL = "goal"
    SAVED = "saved"
    OFF_TARGET = "off_target"
    POST_OR_CROSSBAR = "post_or_crossbar"
    BLOCKED_DEFENDER = "blocked_defender"
    POSSESSION_RETAINED = "possession_retained"
    POSSESSION_LOST = "possession_lost"
    TO_CORNER_OR_THROW = "to_corner_or_throw"


class BodyPart(str, enum.Enum):
    RIGHT_FOOT = "right_foot"
    LEFT_FOOT = "left_foot"
    HEAD = "head"


class PressureState(str, enum.Enum):
    UNDER_PRESSURE = "under_pressure"
    NO_PRESSURE = "no_pressure"


class MatchStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    REVIEWED = "reviewed"
    CLOSED = "closed"
