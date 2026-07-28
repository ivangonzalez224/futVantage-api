"""Pydantic schemas for the matches API."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import AttackDirection, MatchStatus


class MatchCreate(BaseModel):
    team_id: UUID
    opponent_name: str | None = None
    match_date: date | None = None
    video_url: str | None = None
    video_duration_seconds: int | None = None
    attacking_direction_first_half: AttackDirection = AttackDirection.LEFT_TO_RIGHT


class MatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    team_id: UUID
    opponent_name: str | None
    match_date: date | None
    video_url: str | None
    video_duration_seconds: int | None
    status: MatchStatus
    attacking_direction_first_half: AttackDirection
    created_at: datetime
