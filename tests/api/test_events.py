"""API tests for the match events endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Academy, Match, Player, Team


def _build_match_with_player(db_session: Session) -> tuple[Match, Player]:
    academy = Academy(name="Academia Real Peru")
    team = Team(name="Sub-15 A", category="Sub-15", academy=academy)
    player = Player(jersey_number=8, full_name="Diego Ramirez", team=team)
    match = Match(team=team, opponent_name="Rival FC")

    db_session.add(academy)
    db_session.add(match)
    db_session.commit()

    return match, player


def test_creates_an_event_without_destination(client: TestClient, db_session: Session) -> None:
    match, player = _build_match_with_player(db_session)

    response = client.post(
        f"/api/v1/matches/{match.id}/events",
        json={
            "team_id": str(player.team_id),
            "player_id": str(player.id),
            "type": "tackle_duel",
            "result": "won",
            "x_start": "30.00",
            "y_start": "40.00",
            "video_timestamp_seconds": "612.00",
            "half": "first_half",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "tackle_duel"
    assert body["category"] == "duel"
    assert body["x_end"] is None
    assert body["half"] == "first_half"


def test_creates_a_pass_event_with_destination(client: TestClient, db_session: Session) -> None:
    match, player = _build_match_with_player(db_session)

    response = client.post(
        f"/api/v1/matches/{match.id}/events",
        json={
            "team_id": str(player.team_id),
            "player_id": str(player.id),
            "type": "short_pass",
            "result": "completed",
            "x_start": "45.50",
            "y_start": "50.00",
            "x_end": "60.25",
            "y_end": "55.75",
            "video_timestamp_seconds": "1423.14",
            "half": "second_half",
            "pressure": "under_pressure",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "pass"
    assert body["x_end"] == "60.25"
    assert body["pressure"] == "under_pressure"
    assert body["half"] == "second_half"


def test_rejects_a_pass_event_missing_the_destination(
    client: TestClient, db_session: Session
) -> None:
    match, player = _build_match_with_player(db_session)

    response = client.post(
        f"/api/v1/matches/{match.id}/events",
        json={
            "team_id": str(player.team_id),
            "player_id": str(player.id),
            "type": "short_pass",
            "result": "completed",
            "x_start": "45.50",
            "y_start": "50.00",
            "video_timestamp_seconds": "1423.14",
            "half": "first_half",
        },
    )

    assert response.status_code == 422


def test_rejects_an_event_missing_the_half(client: TestClient, db_session: Session) -> None:
    match, player = _build_match_with_player(db_session)

    response = client.post(
        f"/api/v1/matches/{match.id}/events",
        json={
            "team_id": str(player.team_id),
            "player_id": str(player.id),
            "type": "tackle_duel",
            "result": "won",
            "x_start": "30.00",
            "y_start": "40.00",
            "video_timestamp_seconds": "612.00",
        },
    )

    assert response.status_code == 422


def test_returns_404_when_creating_an_event_for_a_missing_match(
    client: TestClient, db_session: Session
) -> None:
    _, player = _build_match_with_player(db_session)
    fake_match_id = "00000000-0000-0000-0000-000000000000"

    response = client.post(
        f"/api/v1/matches/{fake_match_id}/events",
        json={
            "team_id": str(player.team_id),
            "player_id": str(player.id),
            "type": "tackle_duel",
            "result": "won",
            "x_start": "30.00",
            "y_start": "40.00",
            "video_timestamp_seconds": "612.00",
            "half": "first_half",
        },
    )

    assert response.status_code == 404


def test_lists_events_for_a_match_ordered_by_timestamp(
    client: TestClient, db_session: Session
) -> None:
    match, player = _build_match_with_player(db_session)

    for timestamp in ("900.00", "300.00", "600.00"):
        client.post(
            f"/api/v1/matches/{match.id}/events",
            json={
                "team_id": str(player.team_id),
                "player_id": str(player.id),
                "type": "tackle_duel",
                "result": "won",
                "x_start": "30.00",
                "y_start": "40.00",
                "video_timestamp_seconds": timestamp,
                "half": "first_half",
            },
        )

    response = client.get(f"/api/v1/matches/{match.id}/events")

    assert response.status_code == 200
    timestamps = [event["video_timestamp_seconds"] for event in response.json()]
    assert timestamps == ["300.00", "600.00", "900.00"]


def test_returns_404_when_listing_events_for_a_missing_match(
    client: TestClient, db_session: Session
) -> None:
    fake_match_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/api/v1/matches/{fake_match_id}/events")

    assert response.status_code == 404
