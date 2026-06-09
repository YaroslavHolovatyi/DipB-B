# Database Setup — Beer & Beverages

End-to-end checklist to bring the Postgres + PostGIS database up locally and
inspect it from DBeaver.

> Everything below assumes you are in the **project root** (`DiplomaProject/`)
> on a Debian box with Docker and `psql` (client) installed — both are listed
> in your local-setup table.

---

## 1. What this database is

A single Postgres 16 instance running inside Docker (image `postgis/postgis:16-3.4`)
plus a Redis container for cache / pub-sub. The full schema lives in two places
that are **always kept in sync**:

| File | Role |
| --- | --- |
| `database/schema.sql` | Hand-written source of truth — 44 tables, 23 enums, 13 triggers, full PostGIS + full-text setup. |
| `backend/alembic/versions/0001_baseline.py` | Alembic baseline that executes `schema.sql` verbatim on `alembic upgrade head`. |

After this baseline, **all further schema changes go through Alembic revisions**
(see *Adding a migration* below). The raw SQL file is updated in parallel so the
SQL still matches a fresh-clone install.

**What is Alembic?** It's the migration tool that ships with SQLAlchemy. Each
revision is a tiny Python file with `upgrade()` and `downgrade()` functions.
Alembic tracks which revisions a database has applied by writing them to a
`alembic_version` table. That means once your DB is at revision X, running
`alembic upgrade head` only applies the diff between X and the newest revision
— never the whole thing again. The first revision here (`0001_baseline.py`)
just inlines `database/schema.sql` so a fresh DB ends up identical to a
hand-written one.

---

## 2. First-time bring-up

```bash
# 1. Start Postgres + Redis containers (detached)
docker compose up -d

# 2. Wait until the containers report healthy — usually ~5s
docker compose ps

# 3. Apply the baseline schema via Alembic
cd backend
uv run alembic upgrade head
cd ..

# 4. Load all seeds (vibes, Lviv bars, drinks, races, quiz, achievements, dnd classes)
./database/load_seeds.sh
```

That's it — you now have a populated DB.

### Sanity check from the terminal

```bash
# Connect as the app user
PGPASSWORD=app psql -h localhost -U app -d beer_and_beverages

# Inside psql:
\dt                                    -- list all tables
SELECT count(*) FROM bars;             -- ~200 from the Lviv seed
SELECT count(*) FROM races;            -- 8
SELECT count(*) FROM quiz_questions;   -- 10
SELECT count(*) FROM achievements;     -- ~30 (catalogue + per-race)
SELECT count(*) FROM dnd_class_info;   -- 12
\q
```

---

## 3. Connect from DBeaver

1. **Database → New Database Connection** → PostgreSQL
2. Fill in:
   - Host: `localhost`
   - Port: `5432`
   - Database: `beer_and_beverages`
   - Username: `app`
   - Password: `app`
3. *Test Connection* — DBeaver will offer to download the JDBC driver; accept.
4. **Finish.** The schema `public` will appear in the navigator. Expand it to
   see tables, the 23 enum types under *Data Types*, and the 13 triggers per
   table under *Triggers*.

> First time only: DBeaver may warn that the PostGIS-enabled DB has spatial
> columns — pick *Show on map* on a `bars.location` row to see Lviv pins.

---

## 4. Resetting from scratch

```bash
# Stop containers AND wipe the volume (this deletes the data)
docker compose down -v

# Start clean
docker compose up -d
cd backend && uv run alembic upgrade head && cd ..
./database/load_seeds.sh
```

---

## 5. Adding a new migration

When you want to change the schema (add a column, a table, an index, …):

```bash
cd backend

# Create the revision file. Edit it to add upgrade() / downgrade().
uv run alembic revision -m "add foo to bars"

# Apply it
uv run alembic upgrade head

# If you wrote a clean downgrade(), you can roll back the latest revision:
uv run alembic downgrade -1
```

After committing the new revision, **also update `database/schema.sql`** with
the same DDL so that a fresh clone (where someone wants to read the schema
top-to-bottom) stays accurate.

---

## 6. File map

```
DiplomaProject/
├── docker-compose.yml             ← Postgres (with PostGIS) + Redis
├── database/
│   ├── schema.sql                 ← source of truth
│   ├── SCHEMA.md                  ← human-readable schema doc
│   ├── load_seeds.sh              ← applies all seeds/*.sql in order
│   └── seeds/
│       ├── 00_vibes.sql           ← 18 bar atmospheres
│       ├── 01_lviv_bars.sql       ← ~200 OSM-sourced Lviv bars
│       ├── 02_drinks.sql          ← 27 drinks across all drink_type values
│       ├── 03_races.sql           ← 8 fantasy races + race_drinks + race_vibes
│       ├── 04_quiz.sql            ← 10 questions × 4 answers + race scoring
│       ├── 05_achievements.sql    ← ~30 achievements + per-race "Proud …" ones
│       └── 06_dnd_classes.sql     ← 12 D&D 5e classes
└── backend/
    └── alembic/
        ├── env.py                 ← reads DB URL from app.core.config
        └── versions/
            └── 0001_baseline.py   ← inlines schema.sql verbatim
```

---

## 7. Audit changes applied in this pass

These improvements went into `schema.sql` on top of what was already there:

- **`bars.rating_avg` / `rating_count` trigger** — `trg_bar_reviews_refresh_cache`
  on `bar_reviews` keeps the denormalized rating cache in sync after every
  review insert / update / delete. The previous schema documented this trigger
  in a comment but didn't ship it.
- **`dnd_characters.hp_current <= hp_max`** — added `chk_dnd_characters_hp` so
  the AI Dungeon Master can never write a heal that exceeds the cap. Also
  added `hp_current >= 0`, `hp_max > 0`, `armor_class >= 0` checks.
- **Hex-colour format checks** — `races.primary_color` and
  `check_participants.color` now reject anything that isn't `#XXXXXX`.

New seed files added:

- `02_drinks.sql`, `03_races.sql`, `04_quiz.sql`,
  `05_achievements.sql`, `06_dnd_classes.sql`

…and `database/load_seeds.sh` runs all of them in order in one shot.
