"""Endpoints for registering, logging in, and managing the current user."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, Token, UserCreate, UserRead, UserUpdate

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
