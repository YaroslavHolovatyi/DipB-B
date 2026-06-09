"""link checks to the event that produced them (raid OR party)

Revision ID: 0006_event_check_link
Revises: 0005_drink_tags
Create Date: 2026-06-08 00:00:00.000000

WP5 of the finishing plan. A post-gathering shared bill is photographed by the
host and split among the people who actually showed up. To know which gathering
a receipt came from we hang two optional foreign keys on `checks`:

  * raid_id  — the raid this check was rung up at, if any
  * party_id — the party this check was rung up at, if any

Both are nullable so standalone checks (someone scans a bill with no event)
still work exactly as before. A check is tied to at most one event; we don't
enforce that at the DB level since the service only ever sets one.

ON DELETE SET NULL: deleting the event leaves the receipt and its split intact,
it just loses the back-link.

Incremental revision (never edit schema.sql in place).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0006_event_check_link"
down_revision: str | Sequence[str] | None = "0005_drink_tags"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE checks
            ADD COLUMN raid_id  BIGINT REFERENCES raids(id)   ON DELETE SET NULL,
            ADD COLUMN party_id BIGINT REFERENCES parties(id) ON DELETE SET NULL;
        """
    )
    op.execute("CREATE INDEX idx_checks_raid_id  ON checks(raid_id)  WHERE raid_id  IS NOT NULL;")
    op.execute("CREATE INDEX idx_checks_party_id ON checks(party_id) WHERE party_id IS NOT NULL;")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_checks_party_id;")
    op.execute("DROP INDEX IF EXISTS idx_checks_raid_id;")
    op.execute("ALTER TABLE checks DROP COLUMN IF EXISTS party_id;")
    op.execute("ALTER TABLE checks DROP COLUMN IF EXISTS raid_id;")
