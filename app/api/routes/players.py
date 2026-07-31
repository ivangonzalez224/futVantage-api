"""Endpoints for reading, creating, and updating a team's player roster,
plus individual player stats.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.player_stats import compute_player_stats
from app.models.event import Event
from app.models.player import Player
from app.models.team import Team
from app.schemas.player import PlayerCreate, PlayerRead, PlayerUpdate
from app.schemas.player_stats import (
    DefensiveStatsRead,
    DuelStatsRead,
    PassStatsRead,
    PlayerStatsRead,
    PressureStatsRead,
    ShotStatsRead,
)

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


@router.post(
    "/teams/{team_id}/players", response_model=PlayerRead, status_code=status.HTTP_201_CREATED
)
def create_player(team_id: UUID, payload: PlayerCreate, db: Session = Depends(get_db)) -> Player:
    """Adds a player to a team's roster.

    Jersey numbers are unique within a team; reusing one already taken
    on this team returns 409, not a generic validation error.
    """
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    existing_player = db.scalar(
        select(Player).where(
            Player.team_id == team_id, Player.jersey_number == payload.jersey_number
        )
    )
    if existing_player is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Jersey number {payload.jersey_number} is already taken on this team",
        )

    player = Player(
        team_id=team_id,
        jersey_number=payload.jersey_number,
        full_name=payload.full_name,
        position=payload.position,
        birth_date=payload.birth_date,
    )
    db.add(player)
    db.commit()
    db.refresh(player)

    return player


@router.patch("/players/{player_id}", response_model=PlayerRead)
def update_player(player_id: UUID, payload: PlayerUpdate, db: Session = Depends(get_db)) -> Player:
    """Updates a player's roster info.

    Only the fields actually sent in the request body are changed.
    Changing to a jersey number another player on the same team already
    has returns 409, same as creation.
    """
    player = db.get(Player, player_id)
    if player is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    if payload.jersey_number is not None and payload.jersey_number != player.jersey_number:
        existing_player = db.scalar(
            select(Player).where(
                Player.team_id == player.team_id,
                Player.jersey_number == payload.jersey_number,
                Player.id != player_id,
            )
        )
        if existing_player is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Jersey number {payload.jersey_number} is already taken on this team",
            )
        player.jersey_number = payload.jersey_number

    if payload.full_name is not None:
        player.full_name = payload.full_name
    if payload.position is not None:
        player.position = payload.position
    if payload.birth_date is not None:
        player.birth_date = payload.birth_date

    db.commit()
    db.refresh(player)

    return player


@router.get("/players/{player_id}/stats", response_model=PlayerStatsRead)
def get_player_stats(
    player_id: UUID, match_id: UUID | None = None, db: Session = Depends(get_db)
) -> PlayerStatsRead:
    """Returns aggregated performance stats for a player: pass completion,
    duel win rate, shot conversion/accuracy, defensive action retention,
    and a decision-making-under-pressure success rate.

    Pass `match_id` to scope the stats to a single match; omit it to
    aggregate across every match the player has events in.
    """
    player = db.get(Player, player_id)
    if player is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    statement = select(Event).where(Event.player_id == player_id)
    if match_id is not None:
        statement = statement.where(Event.match_id == match_id)
    events = list(db.scalars(statement))

    stats = compute_player_stats(events)

    return PlayerStatsRead(
        player_id=player.id,
        jersey_number=player.jersey_number,
        full_name=player.full_name,
        position=player.position,
        match_id=match_id,
        passes=PassStatsRead.model_validate(stats.passes),
        duels=DuelStatsRead.model_validate(stats.duels),
        shots=ShotStatsRead.model_validate(stats.shots),
        defensive_actions=DefensiveStatsRead.model_validate(stats.defensive_actions),
        pressure=PressureStatsRead.model_validate(stats.pressure),
    )
