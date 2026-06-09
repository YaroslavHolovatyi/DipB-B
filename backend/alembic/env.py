"""
Alembic env — async-aware.

We pull the database URL from `app.core.config.settings.database_sync_url`
(the psycopg-style DSN) so the same `.env` file configures both runtime
and migrations. The async DSN is intentionally NOT used here — Alembic's
runner is sync, and the psycopg driver is the easiest match.

To add a new migration:

    uv run alembic revision -m "add foo table"
    uv run alembic upgrade head

The first migration (`0001_baseline.py`) applies the hand-written
`database/schema.sql` verbatim and stamps the DB at that revision. We will
continue adding incremental migrations on top from here on.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.core.db import Base  # noqa: F401 — imported for `target_metadata`

# Alembic Config object — gives access to the .ini file values.
config = context.config

# Inject our DSN at runtime so we don't duplicate it in alembic.ini.
config.set_main_option("sqlalchemy.url", str(settings.database_sync_url))

# Configure Python logging via alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Used by autogenerate. Once we add ORM models on top of the existing schema,
# they will register themselves on `Base.metadata` via imports below.
# For now we leave it as the raw Base — autogenerate against a schema we
# didn't reflect into ORM will produce noise, so prefer manual revisions.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate SQL for offline application (no live DB connection)."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations against a live DB."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
