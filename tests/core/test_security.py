"""Tests for password hashing and JWT access token utilities."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_password_reset_token,
    hash_password,
    hash_reset_token,
    verify_password,
)


def test_hashed_password_is_not_the_plaintext() -> None:
    hashed = hash_password("correct horse battery staple")

    assert hashed != "correct horse battery staple"
    assert hashed.startswith("$2b$")  # bcrypt hash prefix


def test_verify_password_accepts_the_correct_password() -> None:
    hashed = hash_password("correct horse battery staple")

    assert verify_password("correct horse battery staple", hashed) is True


def test_verify_password_rejects_a_wrong_password() -> None:
    hashed = hash_password("correct horse battery staple")

    assert verify_password("wrong password", hashed) is False


def test_hashing_the_same_password_twice_produces_different_hashes() -> None:
    # bcrypt salts each hash randomly, so two hashes of the same password
    # should never be byte-for-byte identical (this is what makes rainbow
    # table attacks impractical against it).
    first = hash_password("correct horse battery staple")
    second = hash_password("correct horse battery staple")

    assert first != second
    assert verify_password("correct horse battery staple", first) is True
    assert verify_password("correct horse battery staple", second) is True


def test_create_and_decode_access_token_round_trips_the_subject() -> None:
    user_id = uuid4()

    token = create_access_token(user_id)
    decoded_user_id = decode_access_token(token)

    assert decoded_user_id == user_id


def test_decode_access_token_returns_none_for_garbage_input() -> None:
    assert decode_access_token("not-a-real-token") is None


def test_decode_access_token_returns_none_for_an_expired_token() -> None:
    settings = get_settings()
    expired_payload = {
        "sub": str(uuid4()),
        "exp": datetime.now(UTC) - timedelta(minutes=1),
    }
    expired_token = jwt.encode(
        expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )

    assert decode_access_token(expired_token) is None


def test_decode_access_token_returns_none_for_a_token_signed_with_a_different_key() -> None:
    settings = get_settings()
    payload = {"sub": str(uuid4()), "exp": datetime.now(UTC) + timedelta(minutes=5)}
    token_signed_elsewhere = jwt.encode(
        payload, "a-completely-different-secret", algorithm=settings.jwt_algorithm
    )

    assert decode_access_token(token_signed_elsewhere) is None


def test_generate_password_reset_token_returns_a_high_entropy_string() -> None:
    token = generate_password_reset_token()

    assert len(token) >= 32
    # Two calls should never collide in practice.
    assert token != generate_password_reset_token()


def test_hash_reset_token_is_deterministic() -> None:
    # Unlike bcrypt password hashes, this must be deterministic: we need
    # to hash the raw token the user submits and look up that exact hash
    # in the database, so the same input must always hash the same way.
    token = generate_password_reset_token()

    assert hash_reset_token(token) == hash_reset_token(token)


def test_hash_reset_token_differs_for_different_tokens() -> None:
    first_hash = hash_reset_token(generate_password_reset_token())
    second_hash = hash_reset_token(generate_password_reset_token())

    assert first_hash != second_hash


def test_hash_reset_token_does_not_return_the_raw_token() -> None:
    token = generate_password_reset_token()

    assert hash_reset_token(token) != token
