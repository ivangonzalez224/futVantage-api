"""Endpoints for creating, listing, and claiming teams.

Every endpoint here requires authentication: teams are scoped to the
logged-in user (`Team.owner_id`), so the frontend's team picker only
ever shows teams that belong to whoever is logged in.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.academy import Academy
from app.models.team import Team
from app.models.user import User
from app.schemas.team import TeamCreate, TeamRead

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Team:
    """Creates a new team owned by the logged-in user.

    There's no separate "create academy" step in the UI yet, so this
    creates a small academy alongside the team automatically, named
    after it.
    """
    academy = Academy(name=f"{payload.name} Academy")
    team = Team(
        name=payload.name,
        category=payload.category,
        academy=academy,
        owner_id=current_user.id,
    )
    db.add(academy)
    db.add(team)
    db.commit()
    db.refresh(team)

    return team


@router.get("", response_model=list[TeamRead])
def list_my_teams(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Team]:
    """Lists every team owned by the logged-in user, alphabetically by name."""
    statement = select(Team).where(Team.owner_id == current_user.id).order_by(Team.name)
    return list(db.scalars(statement))


@router.patch("/{team_id}/claim", response_model=TeamRead)
def claim_team(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Team:
    """Assigns an "orphan" team (one with no owner yet — e.g. seeded
    before authentication existed) to the logged-in user.

    Returns 409 if the team is already owned by someone else, so an
    account can't silently take over another user's data.
    """
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    if team.owner_id is not None and team.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Team is already owned by another user"
        )

    team.owner_id = current_user.id
    db.commit()
    db.refresh(team)

    return team
