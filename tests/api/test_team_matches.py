"""API tests for the team matches listing endpoint."""

from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Academy, Match, Team


def _build_team(db_session: Session) -> Team:
    academy = Academy(name="Academia Real Peru")
    team = Team(name="Sub-15 A", category="Sub-15", academy=academy)
    db_session.add(academy)
    db_session.commit()
    return team


def test_lists_matches_most_recent_first(client: TestClient, db_session: Session) -> None:
    team = _build_team(db_session)
    now = datetime.now()
    # `created_at` normally comes from a DB server-side clock (see
    # TimestampMixin), which on SQLite only has second-level precision.
    # Two matches created within the same test can end up with an
    # identical timestamp, making the sort order flaky. Setting
    # `created_at` explicitly here keeps the test deterministic.
    older = Match(team=team, opponent_name="Rival A", created_at=now - timedelta(minutes=10))
    db_session.add(older)
    newer = Match(team=team, opponent_name="Rival B", created_at=now)
    db_session.add(newer)
    db_session.commit()

    response = client.get(f"/api/v1/teams/{team.id}/matches")

    assert response.status_code == 200
    opponents = [match["opponent_name"] for match in response.json()]
    assert opponents == ["Rival B", "Rival A"]


def test_returns_full_match_fields(client: TestClient, db_session: Session) -> None:
    team = _build_team(db_session)
    match = Match(team=team, opponent_name="Rival FC", match_date=date(2026, 7, 18))
    db_session.add(match)
    db_session.commit()

    response = client.get(f"/api/v1/teams/{team.id}/matches")

    assert response.status_code == 200
    [body_match] = response.json()
    assert body_match["opponent_name"] == "Rival FC"
    assert body_match["match_date"] == "2026-07-18"
    assert body_match["status"] == "in_progress"


def test_returns_an_empty_list_for_a_team_with_no_matches(
    client: TestClient, db_session: Session
) -> None:
    team = _build_team(db_session)

    response = client.get(f"/api/v1/teams/{team.id}/matches")

    assert response.status_code == 200
    assert response.json() == []


def test_returns_404_for_a_missing_team(client: TestClient, db_session: Session) -> None:
    fake_team_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/api/v1/teams/{fake_team_id}/matches")

    assert response.status_code == 404
