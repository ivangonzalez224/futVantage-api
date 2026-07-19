"""Pydantic schemas for the player stats API response."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PassStatsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total: int
    completed: int
    completion_pct: float | None


class DuelStatsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total: int
    won: int
    win_pct: float | None


class ShotStatsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total: int
    goals: int
    on_target: int
    conversion_pct: float | None
    accuracy_pct: float | None


class DefensiveStatsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total: int
    possession_retained: int
    retention_pct: float | None


class PressureStatsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_under_pressure: int
    successful_under_pressure: int
    success_pct: float | None


class PlayerStatsRead(BaseModel):
    player_id: UUID
    jersey_number: int
    full_name: str
    position: str | None
    match_id: UUID | None
    passes: PassStatsRead
    duels: DuelStatsRead
    shots: ShotStatsRead
    defensive_actions: DefensiveStatsRead
    pressure: PressureStatsRead
