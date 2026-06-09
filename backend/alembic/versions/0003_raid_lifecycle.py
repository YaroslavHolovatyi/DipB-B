"""raid lifecycle — theme, visibility, attendance verification

Revision ID: 0003_raid_lifecycle
Revises: 0002_profile_interests
Create Date: 2026-06-08 00:00:00.000000

WP2 of the finishing plan. Completes the raid lifecycle so an organiser can
run an event end-to-end and the social-rating engine has the data it needs:

  * raids.theme       — optional free-text theme for the gathering
  * raids.visibility  — 'open' (anyone) or 'friends_only' (organiser's friends)

  * raid_status enum gains 'aborted' (host killed it after it started)
  * raid_rsvp_status enum gains the lifecycle states:
        going → arrived → attended | no_show
  * raid_participants.arrived_at  — set when the participant checks in on-site
  * raid_participants.verified_at — set when the host confirms attendance

Incremental revision (never edit schema.sql in place).

NOTE on downgrade: PostgreSQL cannot DROP a value from an enum without
recreating the type, so the added enum values ('aborted', 'arrived',
'attended', 'no_show') are intentionally left in place on downgrade. Only
the columns and the brand-new `raid_visibility` type are reversed. This is
the conventional, safe approach for additive enum migrations.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0003_raid_lifecycle"
down_revision: str | Sequence[str] | None = "0002_profile_interests"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- enum extensions (additive; safe inside the migration tx on PG12+) ---
    op.execute("ALTER TYPE raid_status ADD VALUE IF NOT EXISTS 'aborted';")
    op.execute("ALTER TYPE raid_rsvp_status ADD VALUE IF NOT EXISTS 'arrived';")
    op.execute("ALTER TYPE raid_rsvp_status ADD VALUE IF NOT EXISTS 'attended';")
    op.execute("ALTER TYPE raid_rsvp_status ADD VALUE IF NOT EXISTS 'no_show';")

    # --- visibility enum (brand-new type → usable immediately) ---
    op.execute(
        "CREATE TYPE raid_visibility AS ENUM ('open', 'friends_only');"
    )

    op.execute(
        """
        ALTER TABLE raids
            ADD COLUMN IF NOT EXISTS theme      TEXT,
            ADD COLUMN IF NOT EXISTS visibility raid_visibility NOT NULL DEFAULT 'open';
        """
    )

    op.execute(
        """
        ALTER TABLE raid_participants
            ADD COLUMN IF NOT EXISTS arrived_at  TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS verified_at TIMESTAMPTZ;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE raid_participants
            DROP COLUMN IF EXISTS arrived_at,
            DROP COLUMN IF EXISTS verified_at;
        """
    )
    op.execute(
        """
        ALTER TABLE raids
            DROP COLUMN IF EXISTS theme,
            DROP COLUMN IF EXISTS visibility;
        """
    )
    op.execute("DROP TYPE IF EXISTS raid_visibility;")
    # Added enum values on raid_status / raid_rsvp_status are intentionally
    # left in place (see module docstring).
