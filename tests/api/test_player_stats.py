"""API tests for the player stats endpoint."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Academy, Event, Match, Player, Team
from app.models.enums import EventCategory, EventResult, EventType, MatchHalf, PressureState


def _build_player(db_session: Session) -> tuple[Player, Match]:
    academy = Academy(name="Academia Real Peru")
    team = Team(name="Sub-15 A", category="Sub-15", academy=academy)
    player = Player(jersey_number=8, full_name="Diego Ramirez", team=team)
    match = Match(team=team, opponent_name="Rival FC")
    db_session.add(academy)
    db_session.add(match)
    db_session.commit()
    return player, match


def test_returns_zeroed_stats_for_a_player_with_no_events(
    client: TestClient, db_session: Session
) -> None:
    player, _match = _build_player(db_session)

    response = client.get(f"/api/v1/players/{player.id}/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["passes"] == {"total": 0, "completed": 0, "completion_pct": None}
    assert body["duels"]["total"] == 0


def test_computes_stats_from_the_players_events(client: TestClient, db_session: Session) -> None:
    player, match = _build_player(db_session)
    team = player.team

    events = [
        Event(
            match=match,
            team=team,
            player=player,
            category=EventCategory.PASS,
            type=EventType.SHORT_PASS,
            result=EventResult.COMPLETED,
            x_start=Decimal("30"),
            y_start=Decimal("40"),
            x_end=Decimal("50"),
            y_end=Decimal("40"),
            video_timestamp_seconds=Decimal("100"),
            half=MatchHalf.FIRST_HALF,
            pressure=PressureState.UNDER_PRESSURE,
        ),
        Event(
            match=match,
            team=team,
            player=player,
            category=EventCategory.PASS,
            type=EventType.SHORT_PASS,
            result=EventResult.INTERCEPTED,
            x_start=Decimal("30"),
            y_start=Decimal("40"),
            x_end=Decimal("50"),
            y_end=Decimal("40"),
            video_timestamp_seconds=Decimal("200"),
            half=MatchHalf.FIRST_HALF,
        ),
        Event(
            match=match,
            team=team,
            player=player,
            category=EventCategory.SHOT,
            type=EventType.SHOT_OPEN_PLAY,
            result=EventResult.GOAL,
            x_start=Decimal("85"),
            y_start=Decimal("50"),
            video_timestamp_seconds=Decimal("300"),
            half=MatchHalf.FIRST_HALF,
        ),
    ]
    db_session.add_all(events)
    db_session.commit()

    response = client.get(f"/api/v1/players/{player.id}/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["passes"] == {"total": 2, "completed": 1, "completion_pct": 50.0}
    assert body["shots"]["goals"] == 1
    assert body["pressure"] == {
        "total_under_pressure": 1,
        "successful_under_pressure": 1,
        "success_pct": 100.0,
    }


def test_scopes_stats_to_a_single_match_when_match_id_is_given(
    client: TestClient, db_session: Session
) -> None:
    player, match_one = _build_player(db_session)
    team = player.team
    match_two = Match(team=team, opponent_name="Otro Rival")
    db_session.add(match_two)
    db_session.commit()

    db_session.add(
        Event(
            match=match_one,
            team=team,
            player=player,
            category=EventCategory.DUEL,
            type=EventType.TACKLE_DUEL,
            result=EventResult.WON,
            x_start=Decimal("30"),
            y_start=Decimal("40"),
            video_timestamp_seconds=Decimal("100"),
            half=MatchHalf.FIRST_HALF,
        )
    )
    db_session.add(
        Event(
            match=match_two,
            team=team,
            player=player,
            category=EventCategory.DUEL,
            type=EventType.TACKLE_DUEL,
            result=EventResult.LOST,
            x_start=Decimal("30"),
            y_start=Decimal("40"),
            video_timestamp_seconds=Decimal("100"),
            half=MatchHalf.FIRST_HALF,
        )
    )
    db_session.commit()

    response = client.get(f"/api/v1/players/{player.id}/stats?match_id={match_one.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["duels"] == {"total": 1, "won": 1, "win_pct": 100.0}


def test_returns_404_for_a_missing_player(client: TestClient, db_session: Session) -> None:
    fake_player_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/api/v1/players/{fake_player_id}/stats")

    assert response.status_code == 404
