"""Endpoints for tracking and reading ball possession per match."""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.possession import compute_possession_split
from app.models.enums import MatchHalf
from app.models.match import Match
from app.models.match_possession import MatchPossession
from app.schemas.possession import (
    PossessionHalfRead,
    PossessionLockRead,
    PossessionLockRequest,
    PossessionRead,
    PossessionResetRequest,
    PossessionTotalsRead,
    PossessionUpdateRequest,
)

router = APIRouter(tags=["possession"])


def _get_or_create_possession_row(db: Session, match_id: UUID, half: MatchHalf) -> MatchPossession:
    """Fetches the possession row for a (match, half), creating a
    zeroed-out one if it doesn't exist yet — so callers never have to
    special-case "no row yet" separately from "row with 0 seconds".
    """
    row = db.scalar(
        select(MatchPossession).where(
            MatchPossession.match_id == match_id, MatchPossession.half == half
        )
    )
    if row is None:
        row = MatchPossession(match_id=match_id, half=half)
        db.add(row)
    return row


def _build_possession_read(db: Session, match: Match) -> PossessionRead:
    first_half_row = _get_or_create_possession_row(db, match.id, MatchHalf.FIRST_HALF)
    second_half_row = _get_or_create_possession_row(db, match.id, MatchHalf.SECOND_HALF)
    db.commit()
    db.refresh(first_half_row)
    db.refresh(second_half_row)

    first_split = compute_possession_split(
        first_half_row.team_seconds, first_half_row.opponent_seconds
    )
    second_split = compute_possession_split(
        second_half_row.team_seconds, second_half_row.opponent_seconds
    )
    total_split = compute_possession_split(
        first_half_row.team_seconds + second_half_row.team_seconds,
        first_half_row.opponent_seconds + second_half_row.opponent_seconds,
    )

    return PossessionRead(
        match_id=match.id,
        tracking_locked=match.possession_tracking_locked,
        first_half=PossessionHalfRead(
            half=MatchHalf.FIRST_HALF,
            team_seconds=first_half_row.team_seconds,
            opponent_seconds=first_half_row.opponent_seconds,
            team_pct=first_split.team_pct,
            opponent_pct=first_split.opponent_pct,
            last_video_timestamp_seconds=first_half_row.last_video_timestamp_seconds,
        ),
        second_half=PossessionHalfRead(
            half=MatchHalf.SECOND_HALF,
            team_seconds=second_half_row.team_seconds,
            opponent_seconds=second_half_row.opponent_seconds,
            team_pct=second_split.team_pct,
            opponent_pct=second_split.opponent_pct,
            last_video_timestamp_seconds=second_half_row.last_video_timestamp_seconds,
        ),
        total=PossessionTotalsRead(
            team_seconds=total_split.team_seconds,
            opponent_seconds=total_split.opponent_seconds,
            team_pct=total_split.team_pct,
            opponent_pct=total_split.opponent_pct,
        ),
    )


@router.get("/matches/{match_id}/possession", response_model=PossessionRead)
def get_possession(match_id: UUID, db: Session = Depends(get_db)) -> PossessionRead:
    """Returns the possession split for both halves and the match total.

    Creates zeroed-out possession rows on first read if none exist yet
    — a brand new match has "0% / 0%" possession, not a missing record.
    """
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    return _build_possession_read(db, match)


@router.patch("/matches/{match_id}/possession", response_model=PossessionRead)
def update_possession(
    match_id: UUID, payload: PossessionUpdateRequest, db: Session = Depends(get_db)
) -> PossessionRead:
    """Updates the possession seconds for one half.

    Called automatically by the frontend on every possession toggle and
    every video pause — not something the analyst fills in directly.
    Rejected with 409 once tracking has been locked for this match, so
    a stray click after "finalizar seguimiento" can't silently change
    numbers that were already sealed.
    """
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    if match.possession_tracking_locked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Possession tracking is locked for this match",
        )

    row = _get_or_create_possession_row(db, match_id, payload.half)
    row.team_seconds = payload.team_seconds
    row.opponent_seconds = payload.opponent_seconds
    row.last_video_timestamp_seconds = payload.last_video_timestamp_seconds

    return _build_possession_read(db, match)


@router.post("/matches/{match_id}/possession/reset", response_model=PossessionRead)
def reset_possession(
    match_id: UUID, payload: PossessionResetRequest, db: Session = Depends(get_db)
) -> PossessionRead:
    """Resets one half's possession back to 0/0 seconds.

    Deliberately does nothing beyond that — no attempt to infer "where
    to resume counting from". It's on the analyst to rewind the video
    themselves if they want the recount to be accurate.
    """
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    if match.possession_tracking_locked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Possession tracking is locked for this match",
        )

    row = _get_or_create_possession_row(db, match_id, payload.half)
    row.team_seconds = Decimal("0")
    row.opponent_seconds = Decimal("0")
    row.last_video_timestamp_seconds = None

    return _build_possession_read(db, match)


@router.patch("/matches/{match_id}/possession/lock", response_model=PossessionLockRead)
def set_possession_lock(
    match_id: UUID, payload: PossessionLockRequest, db: Session = Depends(get_db)
) -> PossessionLockRead:
    """Locks or unlocks possession tracking for a match."""
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    match.possession_tracking_locked = payload.locked
    db.commit()
    db.refresh(match)

    return PossessionLockRead(tracking_locked=match.possession_tracking_locked)
