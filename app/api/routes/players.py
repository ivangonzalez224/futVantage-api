"""Endpoints for reading a team's player roster."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.player import Player
from app.models.team import Team
from app.schemas.player import PlayerRead

router = APIRouter(tags=["players"])


@router.get("/teams/{team_id}/players", response_model=list[PlayerRead])
def list_team_players(team_id: UUID, db: Session = Depends(get_db)) -> list[Player]:
    """Lists every player on a team's roster, ordered by jersey number.

    This is what the frontend's annotation UI calls to populate the
    dorsal lookup, instead of relying on a hardcoded player list.
    """
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    statement = select(Player).where(Player.team_id == team_id).order_by(Player.jersey_number)
    return list(db.scalars(statement))
