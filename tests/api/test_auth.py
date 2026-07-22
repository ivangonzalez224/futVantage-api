"""API tests for the authentication endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User


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
