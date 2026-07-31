"""API tests for the match possession endpoints."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Academy, Match, MatchPossession, Team


def _build_match(db_session: Session) -> Match:
    academy = Academy(name="Academia Real Peru")
    team = Team(name="Sub-15 A", category="Sub-15", academy=academy)
    match = Match(team=team, opponent_name="Rival FC")
    db_session.add(academy)
    db_session.add(match)
    db_session.commit()
    return match


def test_returns_zeroed_possession_for_a_brand_new_match(
    client: TestClient, db_session: Session
) -> None:
    match = _build_match(db_session)

    response = client.get(f"/api/v1/matches/{match.id}/possession")

    assert response.status_code == 200
    body = response.json()
    assert body["tracking_locked"] is False
    assert body["first_half"]["team_pct"] is None
    assert body["total"]["team_pct"] is None


def test_returns_404_for_a_missing_match(client: TestClient, db_session: Session) -> None:
    fake_match_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/api/v1/matches/{fake_match_id}/possession")

    assert response.status_code == 404


def test_updates_possession_for_one_half(client: TestClient, db_session: Session) -> None:
    match = _build_match(db_session)

    response = client.patch(
        f"/api/v1/matches/{match.id}/possession",
        json={
            "half": "first_half",
            "team_seconds": "300.00",
            "opponent_seconds": "300.00",
            "last_video_timestamp_seconds": "612.00",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["first_half"]["team_pct"] == 50.0
    assert body["first_half"]["last_video_timestamp_seconds"] == "612.00"
    assert body["second_half"]["team_pct"] is None


def test_combines_both_halves_into_the_total(client: TestClient, db_session: Session) -> None:
    match = _build_match(db_session)

    client.patch(
        f"/api/v1/matches/{match.id}/possession",
        json={"half": "first_half", "team_seconds": "600.00", "opponent_seconds": "300.00"},
    )
    response = client.patch(
        f"/api/v1/matches/{match.id}/possession",
        json={"half": "second_half", "team_seconds": "300.00", "opponent_seconds": "600.00"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"]["team_seconds"] == "900.00"
    assert body["total"]["opponent_seconds"] == "900.00"
    assert body["total"]["team_pct"] == 50.0


def test_rejects_updating_possession_when_locked(client: TestClient, db_session: Session) -> None:
    match = _build_match(db_session)
    client.patch(f"/api/v1/matches/{match.id}/possession/lock", json={"locked": True})

    response = client.patch(
        f"/api/v1/matches/{match.id}/possession",
        json={"half": "first_half", "team_seconds": "10.00", "opponent_seconds": "10.00"},
    )

    assert response.status_code == 409


def test_resets_a_half_back_to_zero(client: TestClient, db_session: Session) -> None:
    match = _build_match(db_session)
    client.patch(
        f"/api/v1/matches/{match.id}/possession",
        json={"half": "first_half", "team_seconds": "300.00", "opponent_seconds": "100.00"},
    )

    response = client.post(
        f"/api/v1/matches/{match.id}/possession/reset", json={"half": "first_half"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["first_half"]["team_seconds"] == "0.00"
    assert body["first_half"]["opponent_seconds"] == "0.00"
    assert body["first_half"]["last_video_timestamp_seconds"] is None
    assert body["first_half"]["team_pct"] is None


def test_resetting_one_half_does_not_affect_the_other(
    client: TestClient, db_session: Session
) -> None:
    match = _build_match(db_session)
    client.patch(
        f"/api/v1/matches/{match.id}/possession",
        json={"half": "second_half", "team_seconds": "200.00", "opponent_seconds": "200.00"},
    )

    response = client.post(
        f"/api/v1/matches/{match.id}/possession/reset", json={"half": "first_half"}
    )

    assert response.status_code == 200
    assert response.json()["second_half"]["team_pct"] == 50.0


def test_rejects_reset_when_locked(client: TestClient, db_session: Session) -> None:
    match = _build_match(db_session)
    client.patch(f"/api/v1/matches/{match.id}/possession/lock", json={"locked": True})

    response = client.post(
        f"/api/v1/matches/{match.id}/possession/reset", json={"half": "first_half"}
    )

    assert response.status_code == 409


def test_locks_and_unlocks_tracking(client: TestClient, db_session: Session) -> None:
    match = _build_match(db_session)

    lock_response = client.patch(
        f"/api/v1/matches/{match.id}/possession/lock", json={"locked": True}
    )
    assert lock_response.status_code == 200
    assert lock_response.json()["tracking_locked"] is True

    unlock_response = client.patch(
        f"/api/v1/matches/{match.id}/possession/lock", json={"locked": False}
    )
    assert unlock_response.status_code == 200
    assert unlock_response.json()["tracking_locked"] is False


def test_locking_does_not_touch_the_possession_numbers(
    client: TestClient, db_session: Session
) -> None:
    match = _build_match(db_session)
    client.patch(
        f"/api/v1/matches/{match.id}/possession",
        json={"half": "first_half", "team_seconds": "150.00", "opponent_seconds": "50.00"},
    )

    client.patch(f"/api/v1/matches/{match.id}/possession/lock", json={"locked": True})

    row = db_session.query(MatchPossession).filter_by(match_id=match.id, half="first_half").one()
    assert row.team_seconds == Decimal("150.00")
