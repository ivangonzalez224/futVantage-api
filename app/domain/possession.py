"""Pure ball-possession percentage calculations.

Kept separate from the ORM/API layers so the arithmetic — especially
the rounding rule that keeps both percentages summing to exactly 100 —
is trivial to unit test without touching a database.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PossessionSplit:
    team_seconds: Decimal
    opponent_seconds: Decimal
    team_pct: float | None
    opponent_pct: float | None


def compute_possession_split(team_seconds: Decimal, opponent_seconds: Decimal) -> PossessionSplit:
    """Computes each side's share of total tracked possession time.

    Returns `None` for both percentages when no time has been tracked
    yet (0 seconds total) — there's no meaningful split to report, and
    dividing by zero would be undefined anyway.

    `opponent_pct` is derived as `100 - team_pct`, not rounded
    independently, so the two always sum to exactly 100. Rounding both
    sides separately is a classic bug: 51.3% and 48.6% (each correctly
    rounded on its own) would display as "51.3% + 48.6% = 99.9%",
    which looks broken to anyone glancing at the numbers.
    """
    total_seconds = team_seconds + opponent_seconds

    if total_seconds <= 0:
        return PossessionSplit(
            team_seconds=team_seconds,
            opponent_seconds=opponent_seconds,
            team_pct=None,
            opponent_pct=None,
        )

    team_pct = round(float(team_seconds / total_seconds) * 100, 1)
    opponent_pct = round(100 - team_pct, 1)

    return PossessionSplit(
        team_seconds=team_seconds,
        opponent_seconds=opponent_seconds,
        team_pct=team_pct,
        opponent_pct=opponent_pct,
    )
