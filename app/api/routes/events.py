"""Endpoints for registering and listing match events."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.event_catalog import get_event_type_rules
from app.models.event import Event
from app.models.match import Match
from app.schemas.event import EventCreate, EventRead

router = APIRouter(tags=["events"])


@router.post(
    "/matches/{match_id}/events",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
)
def create_event(match_id: UUID, payload: EventCreate, db: Session = Depends(get_db)) -> Event:
    """Registers a new event for a match.

    `payload` has already been validated against the event catalog by
    `EventCreate` (destination requirements, valid results, body part,
    pressure tag) before this handler runs.
    """
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    rules = get_event_type_rules(payload.type)

    event = Event(
        match_id=match_id,
        team_id=payload.team_id,
        player_id=payload.player_id,
        category=rules.category,
        type=payload.type,
        result=payload.result,
        x_start=payload.x_start,
        y_start=payload.y_start,
        x_end=payload.x_end,
        y_end=payload.y_end,
        video_timestamp_seconds=payload.video_timestamp_seconds,
        half=payload.half,
        pressure=payload.pressure,
        body_part=payload.body_part,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return event


@router.get("/matches/{match_id}/events", response_model=list[EventRead])
def list_events(match_id: UUID, db: Session = Depends(get_db)) -> list[Event]:
    """Lists every event registered for a match, ordered by video timestamp."""
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    statement = (
        select(Event).where(Event.match_id == match_id).order_by(Event.video_timestamp_seconds)
    )
    return list(db.scalars(statement))
