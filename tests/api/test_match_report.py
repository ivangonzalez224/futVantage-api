"""API tests for the match report endpoint."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Academy, Event, Match, Player, Team
from app.models.enums import EventCategory, EventResult, EventType, MatchHalf, PressureState


def _build_match(db_session: Session) -> tuple[Match, Player]:
    academy = Academy(name="Academia Real Peru")
    team = Team(name="Sub-15 A", category="Sub-15", academy=academy)
    player = Player(jersey_number=8, full_name="Diego Ramirez", team=team)
    match = Match(team=team, opponent_name="Rival FC")
    db_session.add(academy)
    db_session.add(match)
    db_session.commit()
    return match, player


def test_returns_zeroed_report_for_a_match_with_no_events(
    client: TestClient, db_session: Session
) -> None:
    match, _player = _build_match(db_session)

    response = client.get(f"/api/v1/matches/{match.id}/report")

    assert response.status_code == 200
    body = response.json()
    assert body["total_events"] == 0
    assert body["team_totals"]["passes"] == {"total": 0, "completed": 0, "completion_pct": None}
    assert body["set_pieces"] == {"total": 0, "successful": 0, "effectiveness_pct": None}
    assert body["attack_flow"] == {"left_band": 0, "center": 0, "right_band": 0, "total": 0}
    assert body["possession_loss_zones"] == []


def test_aggregates_team_totals_set_pieces_and_loss_zones(
    client: TestClient, db_session: Session
) -> None:
    match, player = _build_match(db_session)
    team = player.team

    events = [
        Event(
            match=match,
            team=team,
            player=player,
            category=EventCategory.PASS,
            type=EventType.SHORT_PASS,
            result=EventResult.INTERCEPTED,
            x_start=Decimal("40"),
            y_start=Decimal("20"),
            x_end=Decimal("55"),
            y_end=Decimal("20"),
            video_timestamp_seconds=Decimal("100"),
            half=MatchHalf.FIRST_HALF,
            pressure=PressureState.UNDER_PRESSURE,
        ),
        Event(
            match=match,
            team=team,
            player=player,
            category=EventCategory.SET_PIECE,
            type=EventType.PENALTY_KICK,
            result=EventResult.GOAL,
            x_start=Decimal("89"),
            y_start=Decimal("50"),
            video_timestamp_seconds=Decimal("200"),
            half=MatchHalf.FIRST_HALF,
            body_part="right_foot",
        ),
    ]
    db_session.add_all(events)
    db_session.commit()

    response = client.get(f"/api/v1/matches/{match.id}/report")

    assert response.status_code == 200
    body = response.json()
    assert body["total_events"] == 2
    assert body["team_totals"]["passes"]["total"] == 1
    assert body["team_totals"]["shots"]["goals"] == 1
    assert body["set_pieces"] == {"total": 1, "successful": 1, "effectiveness_pct": 100.0}
    assert body["attack_flow"]["left_band"] == 1  # y=20
    assert body["attack_flow"]["center"] == 1  # y=50
    assert len(body["possession_loss_zones"]) == 1
    assert body["possession_loss_zones"][0]["under_pressure"] is True


def test_returns_404_for_a_missing_match(client: TestClient, db_session: Session) -> None:
    fake_match_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/api/v1/matches/{fake_match_id}/report")

    assert response.status_code == 404
