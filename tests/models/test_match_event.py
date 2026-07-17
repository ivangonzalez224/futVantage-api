"""Tests for the Match and Event models: defaults, relationships and the
normalized coordinate/enum columns.
"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Academy, Event, Match, Player, Team
from app.models.enums import EventCategory, EventResult, EventType, MatchStatus, PressureState


def _build_team(db_session: Session) -> Team:
    academy = Academy(name="Academia Real Peru")
    team = Team(name="Sub-15 A", category="Sub-15", academy=academy)
    db_session.add(academy)
    return team


def test_match_defaults_to_in_progress_status(db_session: Session) -> None:
    team = _build_team(db_session)
    match = Match(team=team, opponent_name="Rival FC")

    db_session.add(match)
    db_session.commit()

    assert match.status == MatchStatus.IN_PROGRESS


def test_creates_an_event_with_relationships_and_normalized_coordinates(
    db_session: Session,
) -> None:
    team = _build_team(db_session)
    player = Player(jersey_number=8, full_name="Diego Ramirez", team=team)
    match = Match(team=team, opponent_name="Rival FC")

    event = Event(
        match=match,
        team=team,
        player=player,
        category=EventCategory.PASS,
        type=EventType.SHORT_PASS,
        result=EventResult.COMPLETED,
        x_start=Decimal("45.50"),
        y_start=Decimal("50.00"),
        x_end=Decimal("60.25"),
        y_end=Decimal("55.75"),
        video_timestamp_seconds=Decimal("1423.14"),
        pressure=PressureState.UNDER_PRESSURE,
    )

    db_session.add(match)
    db_session.add(event)
    db_session.commit()

    assert event in match.events
    assert event.team is team
    assert event.player is player
    assert event.x_start == Decimal("45.50")
    assert event.video_timestamp_seconds == Decimal("1423.14")
    assert event.pressure == PressureState.UNDER_PRESSURE
    assert event.body_part is None


def test_event_without_destination_leaves_x_end_and_y_end_null(db_session: Session) -> None:
    team = _build_team(db_session)
    player = Player(jersey_number=6, full_name="Renzo Aguilar", team=team)
    match = Match(team=team, opponent_name="Rival FC")

    event = Event(
        match=match,
        team=team,
        player=player,
        category=EventCategory.DUEL,
        type=EventType.TACKLE_DUEL,
        result=EventResult.WON,
        x_start=Decimal("30.00"),
        y_start=Decimal("40.00"),
        video_timestamp_seconds=Decimal("612.00"),
    )

    db_session.add(match)
    db_session.add(event)
    db_session.commit()

    assert event.x_end is None
    assert event.y_end is None


def test_enum_columns_round_trip_correctly(db_session: Session) -> None:
    team = _build_team(db_session)
    player = Player(jersey_number=9, full_name="Luis Torres", team=team)
    match = Match(team=team, opponent_name="Rival FC")

    event = Event(
        match=match,
        team=team,
        player=player,
        category=EventCategory.SHOT,
        type=EventType.SHOT_OPEN_PLAY,
        result=EventResult.GOAL,
        x_start=Decimal("88.00"),
        y_start=Decimal("50.00"),
        video_timestamp_seconds=Decimal("2001.50"),
    )

    db_session.add(match)
    db_session.add(event)
    db_session.commit()
    db_session.expire_all()  # force a fresh read from the database

    fetched = db_session.get(Event, event.id)
    assert fetched is not None
    assert fetched.category is EventCategory.SHOT
    assert fetched.type is EventType.SHOT_OPEN_PLAY
    assert fetched.result is EventResult.GOAL
