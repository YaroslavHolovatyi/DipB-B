# How to Run & Test — Tavern Tales

A start-to-finish guide for bringing the app up locally and verifying it works:
the backend (FastAPI), the database (PostgreSQL + PostGIS) and Redis in Docker,
and the mobile app (Expo) on your phone. Covers automated tests and a manual
end-to-end checklist using the mock admin user.

Two terminals are assumed: one for the **backend** (`backend/`) and one for the
**mobile** app (`mobile/`). All paths are relative to the repo root unless noted.

---

## 1. Prerequisites

You need these installed once (see the project spec / `SETUP.md` for details):

- **Docker + Docker Compose** — runs Postgres (PostGIS) and Redis
- **Python 3.12 + uv** — backend runtime and package manager
- **Node.js 22 LTS** — Expo dev server
- **Expo Go** on your phone (App Store / Play Store) — loads the app over a QR code
- **psql** (optional) — to inspect the database directly

Quick check that the toolchain is present:

```bash
docker compose version && uv --version && node -v && psql --version
```

---

## 2. One-time setup

### 2.1 Backend environment file

The backend reads secrets from `backend/.env`. If it doesn't exist yet, copy the
template and fill it in:

```bash
cd backend
cp .env.example .env
# generate a JWT secret:
python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(64))"
```

Leaving `OPENAI_API_KEY` **empty is fine** — the OCR and Tavern-Tales services
fall back to deterministic stubs, so the whole flow works without spending
tokens. Set it only when you want real receipt parsing / AI narration.

### 2.2 Start Postgres + Redis

From the repo root:

```bash
docker compose up -d
docker compose ps        # both bb_postgres and bb_redis should be "healthy"
```

### 2.3 Create the schema and seed data

```bash
cd backend
uv sync                      # install backend dependencies into .venv
uv run alembic upgrade head  # creates every table (applies database/schema.sql)
cd ..
./database/load_seeds.sh     # cities, bars, races, quiz questions, drinks, achievements
```

Order matters: the seeds add the **Lviv city**, the **races**, and the **quiz
questions** that the signup screen, the admin script, and the race quiz all
depend on.

### 2.4 Create the mock admin user

```bash
cd backend
uv run python scripts/create_admin.py
```

Default login (idempotent — re-run any time to reset it):

```
email:    admin@tavern.test
password: admin1234
```

The admin is created with a race already assigned, so it skips the onboarding
quiz and lands straight in the app.

### 2.5 Verify the database is ready

```bash
psql postgresql://app:app@localhost:5432/beer_and_beverages \
  -c '\dx' \
  -c 'select count(*) as cities from cities;' \
  -c 'select count(*) as races  from races;' \
  -c 'select count(*) as quiz_questions from quiz_questions;' \
  -c "select email, role from users where role='admin';"
```

You should see `postgis` listed in the extensions, non-zero counts, and the
admin row. If `psql` can't connect, the container isn't up (step 2.2).

---

## 3. Run the backend

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Interactive API docs: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health> (or whatever the health router exposes)

`--host 0.0.0.0` is important so your phone can reach the API over the LAN.

---

## 4. Run the mobile app

```bash
cd mobile
npm install        # first time only
npm start          # starts the Expo dev server + QR code
```

Then open **Expo Go** on your phone and scan the QR code (phone and laptop must
be on the same Wi-Fi).

**Pointing the app at your backend.** The app auto-detects your laptop's IP from
the Expo dev server and calls `http://<your-ip>:8000`. If that doesn't resolve,
set it explicitly before `npm start`:

```bash
EXPO_PUBLIC_API_BASE_URL=http://192.168.0.42:8000 npm start   # use your laptop's LAN IP
```

Find your IP with `ip addr` (Linux) or `ipconfig` / `ifconfig`.

---

## 5. Automated tests

### Backend (pytest)

The suite runs against the live Docker Postgres + Redis and rolls back after
each test, so it needs steps 2.2–2.3 done first. It **auto-skips** if those
services aren't reachable.

```bash
cd backend
uv run pytest                 # run everything
uv run pytest -v              # verbose, per-test
uv run pytest --cov=app       # with coverage
uv run pytest tests/test_auth.py::test_login   # a single test
```

Covered today: auth, bars/geo, chat, health, reference data.

### Backend lint & type checks

```bash
cd backend
uv run ruff check .           # lint
uv run ruff format --check .  # formatting
uv run mypy app               # static types (strict)
```

### Mobile type check

```bash
cd mobile
npm run typecheck             # tsc --noEmit — must pass clean
```

---

## 6. Manual end-to-end test (the demo loop)

With the backend and mobile app running, sign in as the admin and walk the core
loop. Each step has an expected result so a failure is obvious.

1. **Login** — open the app, sign in with `admin@tavern.test` / `admin1234`.
   → Lands on the Home feed (no quiz, because the admin already has a race).

2. **New-user onboarding (optional)** — register a brand-new account instead.
   → After signup you're routed into the **Race Quiz**; answer every question,
   tap "Reveal my race", then "Enter the Tavern". → You land in the app with a
   race shown on your profile.

3. **Map** — open the Map tab. → Lviv bar pins load from the PostGIS
   "near me" query. Tapping a pin opens that bar's detail.

4. **Bars** — open the Bars tab, search, favourite a bar.
   → The favourite shows up later on your profile.

5. **Scan a receipt** — Home → "Scan a Receipt" → take/pick a photo → "Create
   check". → A check is created and you enter the split room with parsed line
   items. (With no `OPENAI_API_KEY`, the stub returns a canned Lviv receipt.)

6. **Split + dice** — invite/assign items, then run the d20 "who pays" mechanic.
   → Roll resolves and the kind-soul leaderboard updates.

7. **Tavern Tales** — open the Tavern tab, start a session, send a message.
   → You get an AI Dungeon-Master reply (canned text in stub mode).

8. **Edit profile** — Profile → "Edit" → change your name / city → Save.
   → The change is reflected immediately across the app.

9. **Retake quiz** — Profile → "Retake race quiz".
   → Re-runs the quiz and updates your race.

---

## 7. Building an installable APK (optional, for the demo)

```bash
cd mobile
npm i -g eas-cli
eas login
eas build -p android --profile preview   # produces a downloadable .apk
```

Point the build at a backend your phone can reach (a tunnel such as
`ngrok http 8000`, or a deployed instance) via `EXPO_PUBLIC_API_BASE_URL`.

---

## 8. Troubleshooting

- **`psql`/tests can't connect** — `docker compose ps`; if not healthy,
  `docker compose up -d` and wait for the healthcheck.
- **`relation "users" does not exist`** — run `uv run alembic upgrade head`.
- **Signup shows "No cities available" / quiz is blank** — run
  `./database/load_seeds.sh` (cities + quiz questions weren't seeded).
- **App can't reach the API** — set `EXPO_PUBLIC_API_BASE_URL` to your laptop's
  LAN IP and confirm the backend was started with `--host 0.0.0.0`. `localhost`
  from the phone points at the phone, not your laptop.
- **Admin login fails** — re-run `uv run python scripts/create_admin.py` to
  reset the password; it's safe to run repeatedly.
- **Start completely fresh** — `docker compose down -v` wipes the DB volume;
  then repeat steps 2.2 → 2.4.
