"""add match_possession table and possession_tracking_locked

Revision ID: 163dee006966
Revises: e2c67e11c538
Create Date: 2026-07-29 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "163dee006966"
down_revision: str | None = "e2c67e11c538"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Reuses the "match_half" enum type already created by an earlier
    # migration. `create_type=False` here is the Postgres-specific ENUM
    # class, which — unlike the generic `sa.Enum(..., create_type=False)`
    # — actually skips registering the "create this type" step, so it
    # doesn't attempt (and fail) a CREATE TYPE for a type that already
    # exists.
    match_half_type = PGEnum("first_half", "second_half", name="match_half", create_type=False)

    op.create_table(
        "match_possession",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("match_id", sa.Uuid(), nullable=False),
        sa.Column("half", match_half_type, nullable=False),
        sa.Column("team_seconds", sa.Numeric(8, 2), nullable=False),
        sa.Column("opponent_seconds", sa.Numeric(8, 2), nullable=False),
        sa.Column("last_video_timestamp_seconds", sa.Numeric(8, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_unique_constraint(
        "uq_match_possession_match_half", "match_possession", ["match_id", "half"]
    )

    op.add_column(
        "matches",
        sa.Column(
            "possession_tracking_locked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("matches", "possession_tracking_locked")
    op.drop_table("match_possession")
