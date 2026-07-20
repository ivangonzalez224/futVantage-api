"""Pydantic schemas for the match report API response."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.player_stats import (
    DefensiveStatsRead,
    DuelStatsRead,
    PassStatsRead,
    PressureStatsRead,
    ShotStatsRead,
)


class SetPieceStatsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total: int
    successful: int
    effectiveness_pct: float | None


class AttackFlowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    left_band: int
    center: int
    right_band: int
    total: int


class PossessionLossPointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    x: Decimal
    y: Decimal
    under_pressure: bool


class TeamTotalsRead(BaseModel):
    passes: PassStatsRead
    duels: DuelStatsRead
    shots: ShotStatsRead
    defensive_actions: DefensiveStatsRead
    pressure: PressureStatsRead


class MatchReportRead(BaseModel):
    match_id: UUID
    team_id: UUID
    total_events: int
    team_totals: TeamTotalsRead
    set_pieces: SetPieceStatsRead
    attack_flow: AttackFlowRead
    possession_loss_zones: list[PossessionLossPointRead]
