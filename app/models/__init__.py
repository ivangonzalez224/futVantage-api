"""Imports every ORM model so `Base.metadata` knows about all tables.

This module has no other purpose: Alembic's autogenerate and
`Base.metadata.create_all()` both rely on every model class having been
imported at least once before they run.
"""

from app.models.academy import Academy
from app.models.event import Event
from app.models.match import Match
from app.models.match_possession import MatchPossession
from app.models.password_reset_token import PasswordResetToken
from app.models.player import Player
from app.models.team import Team
from app.models.user import User

__all__ = [
    "Academy",
    "Event",
    "Match",
    "MatchPossession",
    "PasswordResetToken",
    "Player",
    "Team",
    "User",
]
