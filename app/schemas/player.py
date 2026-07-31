"""Pydantic schemas for the players API."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlayerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    team_id: UUID
    jersey_number: int
    full_name: str
    position: str | None
    birth_date: date | None


class PlayerCreate(BaseModel):
    jersey_number: int = Field(ge=1, le=99)
    full_name: str = Field(min_length=1)
    position: str | None = None
    birth_date: date | None = None


class PlayerUpdate(BaseModel):
    """Every field is optional: only the ones actually sent get updated
    (`PATCH` semantics, not `PUT`) — same pattern as `UserUpdate`.
    """

    jersey_number: int | None = Field(default=None, ge=1, le=99)
    full_name: str | None = Field(default=None, min_length=1)
    position: str | None = None
    birth_date: date | None = None
