"""Pydantic schemas for the matches API."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import MatchStatus


class MatchCreate(BaseModel):
    team_id: UUID
    opponent_name: str | None = None
    match_date: date | None = None
    video_url: str | None = None
    video_duration_seconds: int | None = None


class MatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    team_id: UUID
    opponent_name: str | None
    match_date: date | None
    video_url: str | None
    video_duration_seconds: int | None
    status: MatchStatus
    created_at: datetime
