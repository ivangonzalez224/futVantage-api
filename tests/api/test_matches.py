"""API tests for the match creation endpoint."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Academy, Team


def _build_team(db_session: Session) -> Team:
    academy = Academy(name="Academia Real Peru")
    team = Team(name="Sub-15 A", category="Sub-15", academy=academy)
    db_session.add(academy)
    db_session.commit()
    return team


def test_creates_a_match_with_defaults(client: TestClient, db_session: Session) -> None:
    team = _build_team(db_session)

    response = client.post("/api/v1/matches", json={"team_id": str(team.id)})

    assert response.status_code == 201
    body = response.json()
    assert body["team_id"] == str(team.id)
    assert body["status"] == "in_progress"
    assert body["opponent_name"] is None


def test_creates_a_match_with_full_fields(client: TestClient, db_session: Session) -> None:
    team = _build_team(db_session)

    response = client.post(
        "/api/v1/matches",
        json={
            "team_id": str(team.id),
            "opponent_name": "Rival FC",
            "match_date": "2026-07-18",
            "video_url": "https://example.com/match.mp4",
            "video_duration_seconds": 5400,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["opponent_name"] == "Rival FC"
    assert body["match_date"] == "2026-07-18"
    assert body["video_url"] == "https://example.com/match.mp4"
    assert body["video_duration_seconds"] == 5400


def test_returns_404_for_a_missing_team(client: TestClient, db_session: Session) -> None:
    fake_team_id = "00000000-0000-0000-0000-000000000000"

    response = client.post("/api/v1/matches", json={"team_id": fake_team_id})

    assert response.status_code == 404


def test_rejects_a_missing_team_id(client: TestClient, db_session: Session) -> None:
    response = client.post("/api/v1/matches", json={"opponent_name": "Rival FC"})

    assert response.status_code == 422
