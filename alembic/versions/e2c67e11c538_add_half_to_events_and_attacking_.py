"""add half to events and attacking direction to matches

Revision ID: e2c67e11c538
Revises: 92bae3428ce2
Create Date: 2026-07-28 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2c67e11c538"
down_revision: str | None = "92bae3428ce2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


match_half_enum = sa.Enum("first_half", "second_half", name="match_half")
attack_direction_enum = sa.Enum("left_to_right", "right_to_left", name="attack_direction")


def upgrade() -> None:
    # Create the enum types explicitly first. Autogenerate's
    # `op.add_column(..., sa.Enum(...))` doesn't reliably emit the
    # `CREATE TYPE` statement before the `ALTER TABLE ... ADD COLUMN`
    # that references it, which fails with `type "..." does not exist`.
    match_half_enum.create(op.get_bind(), checkfirst=True)
    attack_direction_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "events",
        sa.Column(
            "half",
            sa.Enum("first_half", "second_half", name="match_half", create_type=False),
            nullable=False,
            server_default="first_half",
        ),
    )
    op.add_column(
        "matches",
        sa.Column(
            "attacking_direction_first_half",
            sa.Enum("left_to_right", "right_to_left", name="attack_direction", create_type=False),
            nullable=False,
            server_default="left_to_right",
        ),
    )


def downgrade() -> None:
    op.drop_column("matches", "attacking_direction_first_half")
    op.drop_column("events", "half")

    match_half_enum.drop(op.get_bind(), checkfirst=True)
    attack_direction_enum.drop(op.get_bind(), checkfirst=True)
