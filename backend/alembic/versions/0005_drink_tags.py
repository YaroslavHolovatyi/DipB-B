"""drink tags on raids & parties — powers drink-preference soft ranking

Revision ID: 0005_drink_tags
Revises: 0004_parties
Create Date: 2026-06-08 00:00:00.000000

WP3b of the finishing plan. A user's alcohol preferences are derived from the
race assigned by the onboarding quiz (user.race_id -> race_drinks -> drinks),
so no new user-level table is needed. What's missing is a way to tag an *event*
with the drink types it's about, so discovery can float matching events higher.

  * raid_drinks  — M2M from raids  to the drink_type enum
  * party_drinks — M2M from parties to the drink_type enum

Reuses the existing `drink_type` enum (beer/cocktail/wine/spirit/
non_alcoholic/other) created in the baseline — nothing new to add to it.

Incremental revision (never edit schema.sql in place).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0005_drink_tags"
down_revision: str | Sequence[str] | None = "0004_parties"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE raid_drinks (
            raid_id    BIGINT     NOT NULL REFERENCES raids(id) ON DELETE CASCADE,
            drink_type drink_type NOT NULL,
            PRIMARY KEY (raid_id, drink_type)
        );
        """
    )
    op.execute("CREATE INDEX idx_raid_drinks_type ON raid_drinks(drink_type);")

    op.execute(
        """
        CREATE TABLE party_drinks (
            party_id   BIGINT     NOT NULL REFERENCES parties(id) ON DELETE CASCADE,
            drink_type drink_type NOT NULL,
            PRIMARY KEY (party_id, drink_type)
        );
        """
    )
    op.execute("CREATE INDEX idx_party_drinks_type ON party_drinks(drink_type);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS party_drinks;")
    op.execute("DROP TABLE IF EXISTS raid_drinks;")
