"""API tests for the authentication endpoints."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import PasswordResetToken, User


def test_registers_a_new_user(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "coach@example.com", "password": "supersecret123", "full_name": "Coach"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "coach@example.com"
    assert body["full_name"] == "Coach"
    assert "password" not in body
    assert "hashed_password" not in body


def test_rejects_registration_with_an_already_used_email(
    client: TestClient, db_session: Session
) -> None:
    db_session.add(User(email="coach@example.com", hashed_password=hash_password("supersecret123")))
    db_session.commit()

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "coach@example.com", "password": "anotherpassword"},
    )

    assert response.status_code == 409


def test_rejects_registration_with_a_short_password(
    client: TestClient, db_session: Session
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "coach@example.com", "password": "short"},
    )

    assert response.status_code == 422


def test_logs_in_with_correct_credentials_and_returns_a_token(
    client: TestClient, db_session: Session
) -> None:
    db_session.add(User(email="coach@example.com", hashed_password=hash_password("supersecret123")))
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "coach@example.com", "password": "supersecret123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 0


def test_rejects_login_with_the_wrong_password(client: TestClient, db_session: Session) -> None:
    db_session.add(User(email="coach@example.com", hashed_password=hash_password("supersecret123")))
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "coach@example.com", "password": "wrongpassword"},
    )

    assert response.status_code == 401


def test_rejects_login_for_an_unknown_email(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@example.com", "password": "whatever123"},
    )

    assert response.status_code == 401


def test_returns_the_current_user_with_a_valid_token(
    client: TestClient, db_session: Session
) -> None:
    db_session.add(User(email="coach@example.com", hashed_password=hash_password("supersecret123")))
    db_session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "coach@example.com", "password": "supersecret123"},
    )
    access_token = login_response.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "coach@example.com"


def test_rejects_me_without_a_token(client: TestClient, db_session: Session) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_rejects_me_with_an_invalid_token(client: TestClient, db_session: Session) -> None:
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


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


def test_updates_the_full_name(client: TestClient, db_session: Session) -> None:
    headers = _register_and_login(client)

    response = client.patch("/api/v1/auth/me", json={"full_name": "Ivan Coach"}, headers=headers)

    assert response.status_code == 200
    assert response.json()["full_name"] == "Ivan Coach"


def test_updates_the_email(client: TestClient, db_session: Session) -> None:
    headers = _register_and_login(client)

    response = client.patch(
        "/api/v1/auth/me", json={"email": "new-email@example.com"}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["email"] == "new-email@example.com"


def test_leaves_fields_untouched_when_not_sent(client: TestClient, db_session: Session) -> None:
    headers = _register_and_login(client)
    client.patch("/api/v1/auth/me", json={"full_name": "Ivan Coach"}, headers=headers)

    response = client.patch("/api/v1/auth/me", json={}, headers=headers)

    assert response.status_code == 200
    assert response.json()["full_name"] == "Ivan Coach"
    assert response.json()["email"] == "coach@example.com"


def test_rejects_updating_to_an_email_already_used_by_someone_else(
    client: TestClient, db_session: Session
) -> None:
    _register_and_login(client, email="taken@example.com")
    headers = _register_and_login(client, email="coach@example.com")

    response = client.patch("/api/v1/auth/me", json={"email": "taken@example.com"}, headers=headers)

    assert response.status_code == 409


def test_rejects_profile_update_without_a_token(client: TestClient, db_session: Session) -> None:
    response = client.patch("/api/v1/auth/me", json={"full_name": "Ivan Coach"})

    assert response.status_code == 401


def test_changes_the_password(client: TestClient, db_session: Session) -> None:
    headers = _register_and_login(client)

    response = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "supersecret123", "new_password": "brandnewpassword"},
        headers=headers,
    )
    assert response.status_code == 204

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "coach@example.com", "password": "brandnewpassword"},
    )
    assert login_response.status_code == 200


def test_rejects_password_change_with_the_wrong_current_password(
    client: TestClient, db_session: Session
) -> None:
    headers = _register_and_login(client)

    response = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "wrongpassword", "new_password": "brandnewpassword"},
        headers=headers,
    )

    assert response.status_code == 401


def test_rejects_a_short_new_password(client: TestClient, db_session: Session) -> None:
    headers = _register_and_login(client)

    response = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "supersecret123", "new_password": "short"},
        headers=headers,
    )

    assert response.status_code == 422


def test_rejects_password_change_without_a_token(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "supersecret123", "new_password": "brandnewpassword"},
    )

    assert response.status_code == 401


def test_forgot_password_returns_202_for_an_existing_email(
    client: TestClient, db_session: Session
) -> None:
    _register_and_login(client)

    response = client.post("/api/v1/auth/forgot-password", json={"email": "coach@example.com"})

    assert response.status_code == 202


def test_forgot_password_returns_202_for_an_unknown_email_too(
    client: TestClient, db_session: Session
) -> None:
    # Same response either way, so a client can't use this endpoint to
    # probe which emails have accounts.
    response = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})

    assert response.status_code == 202


def test_forgot_password_creates_a_usable_reset_token(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _register_and_login(client)
    captured: dict[str, str] = {}

    def fake_send_email(to_email: str, reset_token: str) -> None:
        captured["token"] = reset_token

    monkeypatch.setattr("app.api.routes.auth.send_password_reset_email", fake_send_email)

    client.post("/api/v1/auth/forgot-password", json={"email": "coach@example.com"})

    reset_response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": captured["token"], "new_password": "brandnewpassword"},
    )
    assert reset_response.status_code == 204

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "coach@example.com", "password": "brandnewpassword"},
    )
    assert login_response.status_code == 200


def test_forgot_password_does_not_send_an_email_for_an_unknown_address(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    send_calls: list[str] = []
    monkeypatch.setattr(
        "app.api.routes.auth.send_password_reset_email",
        lambda to_email, reset_token: send_calls.append(to_email),
    )

    client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})

    assert send_calls == []


def test_rejects_reset_with_an_invalid_token(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "not-a-real-token", "new_password": "brandnewpassword"},
    )

    assert response.status_code == 400


def test_rejects_reset_with_an_expired_token(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _register_and_login(client)
    captured: dict[str, str] = {}
    monkeypatch.setattr(
        "app.api.routes.auth.send_password_reset_email",
        lambda to_email, reset_token: captured.update(token=reset_token),
    )
    client.post("/api/v1/auth/forgot-password", json={"email": "coach@example.com"})

    # Force the token that was just issued into the past.
    reset_token_row = db_session.scalar(select(PasswordResetToken))
    assert reset_token_row is not None
    reset_token_row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": captured["token"], "new_password": "brandnewpassword"},
    )

    assert response.status_code == 400


def test_rejects_reusing_a_reset_token(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _register_and_login(client)
    captured: dict[str, str] = {}
    monkeypatch.setattr(
        "app.api.routes.auth.send_password_reset_email",
        lambda to_email, reset_token: captured.update(token=reset_token),
    )
    client.post("/api/v1/auth/forgot-password", json={"email": "coach@example.com"})

    first_use = client.post(
        "/api/v1/auth/reset-password",
        json={"token": captured["token"], "new_password": "brandnewpassword"},
    )
    assert first_use.status_code == 204

    second_use = client.post(
        "/api/v1/auth/reset-password",
        json={"token": captured["token"], "new_password": "anotherpassword"},
    )

    assert second_use.status_code == 400


def test_rejects_a_short_new_password_on_reset(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "whatever-token", "new_password": "short"},
    )

    assert response.status_code == 422
