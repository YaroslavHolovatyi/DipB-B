"""
Create (or reset) a mock admin user for local testing.

Idempotent: matched by email. If the user already exists it is updated
(password reset, role set to admin, re-activated, race re-assigned) rather
than duplicated — so you can re-run it any time to get back to a known login.

The user is given a `race_id` so it skips the onboarding race-quiz gate and
lands straight in the app. It is attached to an existing city (defaults to
Lviv, falls back to the first seeded city).

Run from the `backend/` directory, against a migrated + seeded database:

    uv run python scripts/create_admin.py
    # custom credentials:
    uv run python scripts/create_admin.py --email me@test.dev --password secret123 --username boss

Then log in from the app with the printed email (or username) + password.

Requires the same env as the API (DATABASE_URL etc.) — direnv / .env applies.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Make the backend root importable when run as a loose script
# (`python scripts/create_admin.py`), not just as a module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.core.db import AsyncSessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402

DEFAULTS = {
    "email": "admin@tavern.test",
    "username": "admin",
    "password": "admin1234",
    "first_name": "Admin",
    "last_name": "Adventurer",
}


async def _pick_id(db, table: str, preferred_slug: str) -> int | None:
    """Return the id of `preferred_slug` in `table`, else the lowest id, else None."""
    row = await db.execute(
        text(f"SELECT id FROM {table} WHERE slug = :slug LIMIT 1"),
        {"slug": preferred_slug},
    )
    found = row.scalar_one_or_none()
    if found is not None:
        return int(found)
    row = await db.execute(text(f"SELECT id FROM {table} ORDER BY id LIMIT 1"))
    found = row.scalar_one_or_none()
    return int(found) if found is not None else None


async def create_admin(args: argparse.Namespace) -> None:
    async with AsyncSessionLocal() as db:
        city_id = await _pick_id(db, "cities", "lviv")
        if city_id is None:
            raise SystemExit(
                "No cities found. Apply migrations and seed reference data first "
                "(e.g. `alembic upgrade head` + the city/race seed), then re-run."
            )
        race_id = await _pick_id(db, "races", "human")  # optional; skips the quiz gate

        password_hash = hash_password(args.password)

        existing = await db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": args.email},
        )
        user_id = existing.scalar_one_or_none()

        params = {
            "email": args.email,
            "username": args.username,
            "first_name": args.first_name,
            "last_name": args.last_name,
            "password_hash": password_hash,
            "city_id": city_id,
            "race_id": race_id,
        }

        if user_id is None:
            await db.execute(
                text(
                    """
                    INSERT INTO users
                        (first_name, last_name, username, email, password_hash,
                         main_city_id, race_id, role, is_active, email_verified_at)
                    VALUES
                        (:first_name, :last_name, :username, :email, :password_hash,
                         :city_id, :race_id, 'admin', TRUE, now())
                    """
                ),
                params,
            )
            action = "Created"
        else:
            await db.execute(
                text(
                    """
                    UPDATE users SET
                        first_name = :first_name,
                        last_name  = :last_name,
                        username   = :username,
                        password_hash = :password_hash,
                        main_city_id  = :city_id,
                        race_id    = COALESCE(:race_id, race_id),
                        role       = 'admin',
                        is_active  = TRUE,
                        email_verified_at = COALESCE(email_verified_at, now()),
                        deleted_at = NULL
                    WHERE id = :id
                    """
                ),
                {**params, "id": user_id},
            )
            action = "Updated"

        await db.commit()

    print(f"\n  {action} admin user.")
    print("  ---------------------------------------------")
    print(f"  email     : {args.email}")
    print(f"  username  : {args.username}")
    print(f"  password  : {args.password}")
    print("  role      : admin")
    print(f"  city_id   : {city_id}    race_id: {race_id}")
    print("  ---------------------------------------------")
    print("  Log in from the app with the email (or username) + password.\n")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Create/reset a mock admin user.")
    p.add_argument("--email", default=DEFAULTS["email"])
    p.add_argument("--username", default=DEFAULTS["username"])
    p.add_argument("--password", default=DEFAULTS["password"], help="min 8 chars")
    p.add_argument("--first-name", dest="first_name", default=DEFAULTS["first_name"])
    p.add_argument("--last-name", dest="last_name", default=DEFAULTS["last_name"])
    args = p.parse_args()
    if len(args.password) < 8:
        p.error("password must be at least 8 characters (the API enforces this on login).")
    return args


if __name__ == "__main__":
    asyncio.run(create_admin(parse_args()))
