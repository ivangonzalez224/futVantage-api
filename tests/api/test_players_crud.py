"""API tests for creating and updating players."""

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


def test_creates_a_player(client: TestClient, db_session: Session) -> None:
    team = _build_team(db_session)

    response = client.post(
        f"/api/v1/teams/{team.id}/players",
        json={"jersey_number": 9, "full_name": "Mauricio Peña", "position": "Delantero"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["jersey_number"] == 9
    assert body["full_name"] == "Mauricio Peña"
    assert body["position"] == "Delantero"


def test_rejects_a_duplicate_jersey_number_on_the_same_team(
    client: TestClient, db_session: Session
) -> None:
    team = _build_team(db_session)
    client.post(
        f"/api/v1/teams/{team.id}/players", json={"jersey_number": 9, "full_name": "Player A"}
    )

    response = client.post(
        f"/api/v1/teams/{team.id}/players", json={"jersey_number": 9, "full_name": "Player B"}
    )

    assert response.status_code == 409


def test_allows_the_same_jersey_number_on_different_teams(
    client: TestClient, db_session: Session
) -> None:
    team_a = _build_team(db_session)
    academy_b = Academy(name="Academia B")
    team_b = Team(name="Sub-15 B", category="Sub-15", academy=academy_b)
    db_session.add(academy_b)
    db_session.add(team_b)
    db_session.commit()

    response_a = client.post(
        f"/api/v1/teams/{team_a.id}/players", json={"jersey_number": 9, "full_name": "Player A"}
    )
    response_b = client.post(
        f"/api/v1/teams/{team_b.id}/players", json={"jersey_number": 9, "full_name": "Player B"}
    )

    assert response_a.status_code == 201
    assert response_b.status_code == 201


def test_returns_404_when_creating_a_player_for_a_missing_team(
    client: TestClient, db_session: Session
) -> None:
    fake_team_id = "00000000-0000-0000-0000-000000000000"

    response = client.post(
        f"/api/v1/teams/{fake_team_id}/players", json={"jersey_number": 9, "full_name": "Player"}
    )

    assert response.status_code == 404


def test_rejects_an_invalid_jersey_number(client: TestClient, db_session: Session) -> None:
    team = _build_team(db_session)

    response = client.post(
        f"/api/v1/teams/{team.id}/players", json={"jersey_number": 0, "full_name": "Player"}
    )

    assert response.status_code == 422


def test_updates_a_players_full_name(client: TestClient, db_session: Session) -> None:
    team = _build_team(db_session)
    create_response = client.post(
        f"/api/v1/teams/{team.id}/players", json={"jersey_number": 9, "full_name": "Old Name"}
    )
    player_id = create_response.json()["id"]

    response = client.patch(f"/api/v1/players/{player_id}", json={"full_name": "New Name"})

    assert response.status_code == 200
    assert response.json()["full_name"] == "New Name"
    assert response.json()["jersey_number"] == 9


def test_updates_a_players_jersey_number(client: TestClient, db_session: Session) -> None:
    team = _build_team(db_session)
    create_response = client.post(
        f"/api/v1/teams/{team.id}/players", json={"jersey_number": 9, "full_name": "Player"}
    )
    player_id = create_response.json()["id"]

    response = client.patch(f"/api/v1/players/{player_id}", json={"jersey_number": 10})

    assert response.status_code == 200
    assert response.json()["jersey_number"] == 10


def test_rejects_updating_to_a_jersey_number_taken_by_a_teammate(
    client: TestClient, db_session: Session
) -> None:
    team = _build_team(db_session)
    client.post(f"/api/v1/teams/{team.id}/players", json={"jersey_number": 9, "full_name": "A"})
    create_response = client.post(
        f"/api/v1/teams/{team.id}/players", json={"jersey_number": 10, "full_name": "B"}
    )
    player_id = create_response.json()["id"]

    response = client.patch(f"/api/v1/players/{player_id}", json={"jersey_number": 9})

    assert response.status_code == 409


def test_leaves_fields_untouched_when_not_sent(client: TestClient, db_session: Session) -> None:
    team = _build_team(db_session)
    create_response = client.post(
        f"/api/v1/teams/{team.id}/players",
        json={"jersey_number": 9, "full_name": "Player", "position": "Delantero"},
    )
    player_id = create_response.json()["id"]

    response = client.patch(f"/api/v1/players/{player_id}", json={})

    assert response.status_code == 200
    assert response.json()["full_name"] == "Player"
    assert response.json()["position"] == "Delantero"


def test_returns_404_when_updating_a_missing_player(
    client: TestClient, db_session: Session
) -> None:
    fake_player_id = "00000000-0000-0000-0000-000000000000"

    response = client.patch(f"/api/v1/players/{fake_player_id}", json={"full_name": "New"})

    assert response.status_code == 404
