"""Pydantic schemas for the players API."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlayerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    team_id: UUID
    jersey_number: int
    full_name: str
    position: str | None
    birth_date: date | None
