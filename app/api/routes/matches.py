"""Endpoints for creating matches, listing a team's matches, and reading
their team-level report.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.match_report import compute_match_report
from app.models.event import Event
from app.models.match import Match
from app.models.team import Team
from app.schemas.match import MatchCreate, MatchRead, MatchUpdate
from app.schemas.match_report import (
    AttackFlowRead,
    MatchReportRead,
    PossessionLossPointRead,
    SetPieceStatsRead,
    TeamTotalsRead,
)
from app.schemas.player_stats import (
    DefensiveStatsRead,
    DuelStatsRead,
    PassStatsRead,
    PressureStatsRead,
    ShotStatsRead,
)

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
        attacking_direction_first_half=payload.attacking_direction_first_half,
    )
    db.add(match)
    db.commit()
    db.refresh(match)

    return match


@router.get("/teams/{team_id}/matches", response_model=list[MatchRead])
def list_team_matches(team_id: UUID, db: Session = Depends(get_db)) -> list[Match]:
    """Lists every match recorded for a team, most recent first.

    This is what the frontend's dashboard calls to populate a match
    picker, instead of requiring the analyst to paste a match UUID by
    hand.
    """
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    statement = select(Match).where(Match.team_id == team_id).order_by(Match.created_at.desc())
    return list(db.scalars(statement))


@router.get("/matches/{match_id}/report", response_model=MatchReportRead)
def get_match_report(match_id: UUID, db: Session = Depends(get_db)) -> MatchReportRead:
    """Returns the team-level report for a match: overall pass/duel/shot/
    defensive stats, set-piece effectiveness, attack flow by lateral
    band, and possession-loss zones for a heatmap.

    See `app.domain.match_report` for the scope note on why a
    player-to-player pass network isn't included yet.
    """
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    events = list(db.scalars(select(Event).where(Event.match_id == match_id)))
    report = compute_match_report(events)

    return MatchReportRead(
        match_id=match.id,
        team_id=match.team_id,
        total_events=len(events),
        team_totals=TeamTotalsRead(
            passes=PassStatsRead.model_validate(report.team_totals.passes),
            duels=DuelStatsRead.model_validate(report.team_totals.duels),
            shots=ShotStatsRead.model_validate(report.team_totals.shots),
            defensive_actions=DefensiveStatsRead.model_validate(
                report.team_totals.defensive_actions
            ),
            pressure=PressureStatsRead.model_validate(report.team_totals.pressure),
        ),
        set_pieces=SetPieceStatsRead.model_validate(report.set_pieces),
        attack_flow=AttackFlowRead.model_validate(report.attack_flow),
        possession_loss_zones=[
            PossessionLossPointRead.model_validate(point) for point in report.possession_loss_zones
        ],
    )


@router.patch("/matches/{match_id}", response_model=MatchRead)
def update_match(match_id: UUID, payload: MatchUpdate, db: Session = Depends(get_db)) -> Match:
    """Updates a match's editable fields — today, mainly used to attach
    or replace its video URL after the match was already created.

    Sending `video_url: null` explicitly clears it (unlike `PATCH
    /players/{id}`, where omitting a field is what leaves it
    untouched — here, sending the field with a null value is itself
    a meaningful action: "remove the video").
    """
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(match, field, value)

    db.commit()
    db.refresh(match)

    return match
