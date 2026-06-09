"""baseline — apply database/schema.sql verbatim

Revision ID: 0001_baseline
Revises:
Create Date: 2026-05-25 00:00:00.000000

This migration reads the hand-written schema from `database/schema.sql`
(located one level up from the `backend/` directory) and executes it as a
single batch. From this point onward, all schema changes should be made
through additional, incremental Alembic revisions — never by editing
schema.sql in place.

If you ever need to rebuild from scratch:

    docker compose down -v        # wipe the volume
    docker compose up -d
    uv run alembic upgrade head

The downgrade is a destructive "drop everything in public" because we don't
maintain a fine-grained reverse of the baseline.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_baseline"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# `backend/alembic/versions/<this file>` → walk three parents to reach the
# repo root, then into `database/schema.sql`.
SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent / "database" / "schema.sql"
)


def upgrade() -> None:
    if not SCHEMA_PATH.is_file():
        raise FileNotFoundError(
            f"Cannot find baseline schema at {SCHEMA_PATH}. "
            "Did the project layout change?"
        )
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    # Use the raw DBAPI cursor to execute the schema verbatim.
    # op.execute() wraps strings in sqlalchemy.text() which parses bind
    # parameters — our schema comments contain JSON like `"int":10` which
    # SQLAlchemy misreads as a named parameter `10`. Going through the raw
    # psycopg cursor bypasses that parsing entirely.
    bind = op.get_bind()
    cur = bind.connection.connection.cursor()
    cur.execute(sql)
    cur.close()


def downgrade() -> None:
    # Wholesale teardown — fine for a baseline, but never use this pattern
    # for incremental migrations (those should have a precise reverse).
    op.execute(
        """
        DROP SCHEMA public CASCADE;
        CREATE SCHEMA public;
        GRANT ALL ON SCHEMA public TO public;
        """
    )
