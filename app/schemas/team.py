"""Pydantic schemas for the teams API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TeamCreate(BaseModel):
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)


class TeamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    academy_id: UUID
    owner_id: UUID | None
    name: str
    category: str
    created_at: datetime
