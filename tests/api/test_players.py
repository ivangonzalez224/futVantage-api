"""API tests for the team players (roster) endpoint."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Academy, Player, Team


def test_lists_players_ordered_by_jersey_number(client: TestClient, db_session: Session) -> None:
    academy = Academy(name="Academia Real Peru")
    team = Team(name="Sub-15 A", category="Sub-15", academy=academy)
    db_session.add(academy)
    db_session.add(Player(jersey_number=9, full_name="Luis Torres", team=team))
    db_session.add(Player(jersey_number=1, full_name="Mateo Salazar", team=team))
    db_session.add(Player(jersey_number=8, full_name="Diego Ramirez", team=team))
    db_session.commit()

    response = client.get(f"/api/v1/teams/{team.id}/players")

    assert response.status_code == 200
    jersey_numbers = [player["jersey_number"] for player in response.json()]
    assert jersey_numbers == [1, 8, 9]


def test_returns_full_player_fields(client: TestClient, db_session: Session) -> None:
    academy = Academy(name="Academia Real Peru")
    team = Team(name="Sub-15 A", category="Sub-15", academy=academy)
    db_session.add(academy)
    db_session.add(Player(jersey_number=8, full_name="Diego Ramirez", team=team))
    db_session.commit()

    response = client.get(f"/api/v1/teams/{team.id}/players")

    assert response.status_code == 200
    [player] = response.json()
    assert player["full_name"] == "Diego Ramirez"
    assert player["team_id"] == str(team.id)
    assert player["position"] is None
    assert player["birth_date"] is None


def test_returns_an_empty_list_for_a_team_with_no_players(
    client: TestClient, db_session: Session
) -> None:
    academy = Academy(name="Academia Real Peru")
    team = Team(name="Sub-15 A", category="Sub-15", academy=academy)
    db_session.add(academy)
    db_session.commit()

    response = client.get(f"/api/v1/teams/{team.id}/players")

    assert response.status_code == 200
    assert response.json() == []


def test_returns_404_for_a_missing_team(client: TestClient, db_session: Session) -> None:
    fake_team_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/api/v1/teams/{fake_team_id}/players")

    assert response.status_code == 404
