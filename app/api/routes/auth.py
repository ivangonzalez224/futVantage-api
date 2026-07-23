"""Endpoints for registering, logging in, and managing the current user."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.email import send_password_reset_email
from app.core.security import (
    create_access_token,
    generate_password_reset_token,
    hash_password,
    hash_reset_token,
    verify_password,
)
from app.db.session import get_db
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserRead,
    UserUpdate,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    """Creates a new user account.

    Emails are unique across the whole system; attempting to register an
    already-used email returns 409, not a generic validation error, so
    the frontend can show "this email is already registered" instead of
    a confusing 422.
    """
    existing_user = db.scalar(select(User).where(User.email == payload.email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already registered"
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    """Exchanges an email + password for a JWT access token.

    Uses the standard OAuth2 "password" flow shape (form fields named
    `username`/`password`, with `username` holding the email) so
    Swagger's built-in "Authorize" button works against this endpoint
    without any extra configuration.
    """
    invalid_credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = db.scalar(select(User).where(User.email == form_data.username))
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise invalid_credentials_error

    access_token = create_access_token(user.id)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    """Returns the profile of whoever the Bearer token belongs to."""
    return current_user


@router.patch("/me", response_model=UserRead)
def update_current_user(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Updates the logged-in user's profile (`full_name` and/or `email`).

    Only the fields actually sent in the request body are changed —
    omitting a field leaves it untouched. Changing to an email another
    account already uses returns 409, same as registration.
    """
    if payload.email is not None and payload.email != current_user.email:
        existing_user = db.scalar(
            select(User).where(User.email == payload.email, User.id != current_user.id)
        )
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email is already registered"
            )
        current_user.email = payload.email

    if payload.full_name is not None:
        current_user.full_name = payload.full_name

    db.commit()
    db.refresh(current_user)

    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Changes the logged-in user's password.

    Requires the current password to be sent along with the new one —
    a valid access token alone isn't enough to change the password (e.g.
    if someone left a session open on a shared computer).
    """
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect"
        )

    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> None:
    """Starts a password reset: if the email belongs to an account,
    emails a one-time reset link.

    Always returns 202 regardless of whether the email exists — a
    different response for "no account with that email" would let
    anyone probe which emails are registered.
    """
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None:
        return

    settings = get_settings()
    raw_token = generate_password_reset_token()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.password_reset_token_expire_minutes)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_reset_token(raw_token),
        expires_at=expires_at,
    )
    db.add(reset_token)
    db.commit()

    send_password_reset_email(user.email, raw_token)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> None:
    """Completes a password reset using a token from `forgot-password`.

    The token is single-use (rejected once `used_at` is set) and expires
    after `settings.password_reset_token_expire_minutes`. Both failure
    cases return the same generic error, so a client can't distinguish
    "expired" from "already used" from "never existed".
    """
    invalid_token_error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token"
    )

    reset_token = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == hash_reset_token(payload.token)
        )
    )
    if reset_token is None or reset_token.used_at is not None:
        raise invalid_token_error

    # SQLite (used in tests) round-trips a `DateTime(timezone=True)`
    # column as a naive datetime even though Postgres preserves the
    # timezone — normalize before comparing so this works on both.
    expires_at = reset_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < datetime.now(UTC):
        raise invalid_token_error

    user = db.get(User, reset_token.user_id)
    if user is None:
        # Should be unreachable (the FK constraint guarantees the user
        # exists), but an assert here would be silently skipped if
        # Python ever runs with -O, so this defends against that instead.
        raise invalid_token_error

    user.hashed_password = hash_password(payload.new_password)
    reset_token.used_at = datetime.now(UTC)
    db.commit()
