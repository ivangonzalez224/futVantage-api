"""Endpoints for creating matches."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.match import Match
from app.models.team import Team
from app.schemas.match import MatchCreate, MatchRead

router = APIRouter(tags=["matches"])


@router.post("/matches", response_model=MatchRead, status_code=status.HTTP_201_CREATED)
def create_match(payload: MatchCreate, db: Session = Depends(get_db)) -> Match:
    """Creates a new match for a team, defaulting its status to `in_progress`.

    This exists so analysts (and this app's own test/demo tooling) don't
    need to seed matches by hand directly in the database.
    """
    team = db.get(Team, payload.team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    match = Match(
        team_id=payload.team_id,
        opponent_name=payload.opponent_name,
        match_date=payload.match_date,
        video_url=payload.video_url,
        video_duration_seconds=payload.video_duration_seconds,
    )
    db.add(match)
    db.commit()
    db.refresh(match)

    return match
