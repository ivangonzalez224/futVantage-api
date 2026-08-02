"""API tests for updating a match, focused on the video URL fields."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Academy, Team


def _build_team(db_session: Session) -> Team:
    academy = Academy(name="Academia Real Peru")
    team = Team(name="Sub-15 A", category="Sub-15", academy=academy)
    db_session.add(academy)
    db_session.add(team)
    db_session.commit()
    return team


def test_attaches_a_video_url_to_a_match_created_without_one(
    client: TestClient, db_session: Session
) -> None:
    team = _build_team(db_session)
    create_response = client.post("/api/v1/matches", json={"team_id": str(team.id)})
    match_id = create_response.json()["id"]
    assert create_response.json()["video_url"] is None

    response = client.patch(
        f"/api/v1/matches/{match_id}",
        json={"video_url": "https://example.com/videos/match-1.mp4"},
    )

    assert response.status_code == 200
    assert response.json()["video_url"] == "https://example.com/videos/match-1.mp4"


def test_replaces_an_existing_video_url(client: TestClient, db_session: Session) -> None:
    team = _build_team(db_session)
    create_response = client.post(
        "/api/v1/matches",
        json={"team_id": str(team.id), "video_url": "https://example.com/old.mp4"},
    )
    match_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/matches/{match_id}", json={"video_url": "https://example.com/new.mp4"}
    )

    assert response.status_code == 200
    assert response.json()["video_url"] == "https://example.com/new.mp4"


def test_clears_the_video_url_when_sent_explicitly_as_null(
    client: TestClient, db_session: Session
) -> None:
    team = _build_team(db_session)
    create_response = client.post(
        "/api/v1/matches",
        json={"team_id": str(team.id), "video_url": "https://example.com/old.mp4"},
    )
    match_id = create_response.json()["id"]

    response = client.patch(f"/api/v1/matches/{match_id}", json={"video_url": None})

    assert response.status_code == 200
    assert response.json()["video_url"] is None


def test_updates_the_video_duration(client: TestClient, db_session: Session) -> None:
    team = _build_team(db_session)
    create_response = client.post("/api/v1/matches", json={"team_id": str(team.id)})
    match_id = create_response.json()["id"]

    response = client.patch(f"/api/v1/matches/{match_id}", json={"video_duration_seconds": 5400})

    assert response.status_code == 200
    assert response.json()["video_duration_seconds"] == 5400


def test_leaves_other_fields_untouched_when_not_sent(
    client: TestClient, db_session: Session
) -> None:
    team = _build_team(db_session)
    create_response = client.post(
        "/api/v1/matches", json={"team_id": str(team.id), "opponent_name": "Rival FC"}
    )
    match_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/matches/{match_id}", json={"video_url": "https://example.com/video.mp4"}
    )

    assert response.status_code == 200
    assert response.json()["opponent_name"] == "Rival FC"


def test_returns_404_when_updating_a_missing_match(client: TestClient, db_session: Session) -> None:
    fake_match_id = "00000000-0000-0000-0000-000000000000"

    response = client.patch(
        f"/api/v1/matches/{fake_match_id}", json={"video_url": "https://example.com/video.mp4"}
    )

    assert response.status_code == 404
