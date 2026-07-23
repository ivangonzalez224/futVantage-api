"""API tests for the teams endpoints: create, list mine, and claim."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Academy, Team


def _register_and_login(client: TestClient, email: str = "coach@example.com") -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret123"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "supersecret123"},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_creates_a_team_owned_by_the_logged_in_user(
    client: TestClient, db_session: Session
) -> None:
    headers = _register_and_login(client)

    response = client.post(
        "/api/v1/teams", json={"name": "Sub-15 A", "category": "Sub-15"}, headers=headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Sub-15 A"
    assert body["owner_id"] is not None


def test_rejects_team_creation_without_a_token(client: TestClient, db_session: Session) -> None:
    response = client.post("/api/v1/teams", json={"name": "Sub-15 A", "category": "Sub-15"})

    assert response.status_code == 401


def test_lists_only_the_current_users_teams(client: TestClient, db_session: Session) -> None:
    headers_a = _register_and_login(client, email="coach.a@example.com")
    headers_b = _register_and_login(client, email="coach.b@example.com")

    client.post("/api/v1/teams", json={"name": "Team A", "category": "Sub-15"}, headers=headers_a)
    client.post("/api/v1/teams", json={"name": "Team B", "category": "Sub-17"}, headers=headers_b)

    response = client.get("/api/v1/teams", headers=headers_a)

    assert response.status_code == 200
    names = [team["name"] for team in response.json()]
    assert names == ["Team A"]


def test_claims_an_orphan_team(client: TestClient, db_session: Session) -> None:
    academy = Academy(name="Seeded Academy")
    orphan_team = Team(name="Orphan Team", category="Sub-15", academy=academy, owner_id=None)
    db_session.add(academy)
    db_session.add(orphan_team)
    db_session.commit()

    headers = _register_and_login(client)

    response = client.patch(f"/api/v1/teams/{orphan_team.id}/claim", headers=headers)

    assert response.status_code == 200
    assert response.json()["owner_id"] is not None


def test_rejects_claiming_a_team_already_owned_by_someone_else(
    client: TestClient, db_session: Session
) -> None:
    headers_a = _register_and_login(client, email="coach.a@example.com")
    headers_b = _register_and_login(client, email="coach.b@example.com")

    create_response = client.post(
        "/api/v1/teams", json={"name": "Team A", "category": "Sub-15"}, headers=headers_a
    )
    team_id = create_response.json()["id"]

    response = client.patch(f"/api/v1/teams/{team_id}/claim", headers=headers_b)

    assert response.status_code == 409


def test_returns_404_when_claiming_a_missing_team(client: TestClient, db_session: Session) -> None:
    headers = _register_and_login(client)
    fake_team_id = "00000000-0000-0000-0000-000000000000"

    response = client.patch(f"/api/v1/teams/{fake_team_id}/claim", headers=headers)

    assert response.status_code == 404
