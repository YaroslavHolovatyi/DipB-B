"""add a nullable gender to users (drives the m/f race avatar)

Revision ID: 0007_user_gender
Revises: 0006_event_check_link
Create Date: 2026-06-09 00:00:00.000000

The race quiz ends with a gender question so the profile can show the correct
race avatar — every race ships a male (`_m`) and female (`_f`) illustration.

`gender` is a native enum with two labels, `m` and `f`. The column is NULLABLE:
existing users predate the question, and a user can finish onboarding before we
ever ask. The app falls back to the male art when gender is unknown.

Incremental revision (never edit schema.sql in place).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0007_user_gender"
down_revision: str | Sequence[str] | None = "0006_event_check_link"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE TYPE gender AS ENUM ('m', 'f');")
    op.execute("ALTER TABLE users ADD COLUMN gender gender;")


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS gender;")
    op.execute("DROP TYPE IF EXISTS gender;")
