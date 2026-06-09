# Beer & Beverages — Backend

FastAPI backend for the mobile app. Python 3.12, async SQLAlchemy 2 + asyncpg,
PostgreSQL 16 with PostGIS, Redis 7. Managed with `uv`.

## Quick start

```bash
# 0.  Bring up Postgres + Redis (from the project root)
cd ..
docker compose up -d

# 1.  Install dependencies
cd backend
uv sync

# 2.  Copy the env template and fill it in
cp .env.example .env
# (at minimum, set JWT_SECRET to a long random string)

# 3.  Apply the schema baseline migration
uv run alembic upgrade head

# 4.  Start the dev server (auto-reload)
uv run fastapi dev app/main.py
# → http://localhost:8000
# → http://localhost:8000/docs   (Swagger UI)
```

## Layout

```
backend/
├── app/
│   ├── main.py                # FastAPI app, lifespan, router includes
│   ├── core/                  # Cross-cutting infrastructure
│   │   ├── config.py          #   pydantic-settings (.env -> Settings)
│   │   ├── db.py              #   async engine + session factory
│   │   ├── redis.py           #   shared Redis client + lifespan helpers
│   │   ├── security.py        #   Argon2 hashing + JWT encode/decode
│   │   └── deps.py            #   FastAPI dependencies (db, current_user, …)
│   ├── shared/                # Reusable bits not tied to a domain
│   │   ├── exceptions.py
│   │   └── pagination.py
│   ├── auth/                  # signup / login / refresh / logout
│   ├── health/                # /health, /health/db, /health/redis
│   └── realtime/              # WebSocket manager + Redis pub/sub bridge
├── alembic/
│   ├── env.py                 # async-aware Alembic env
│   └── versions/
│       └── 0001_baseline.py   # applies ../database/schema.sql verbatim
├── alembic.ini
├── pyproject.toml             # uv project + tool config (ruff, mypy, pytest)
└── .env.example
```

## Endpoints

### Health
| Method | Path | Notes |
|---|---|---|
| GET | `/health` | Liveness. |
| GET | `/health/db` | `SELECT 1` against Postgres. |
| GET | `/health/redis` | `PING` against Redis. |

### Auth
| Method | Path | Notes |
|---|---|---|
| POST | `/auth/signup` | Create account → tokens + user. |
| POST | `/auth/login` | Email-or-username + password. |
| POST | `/auth/refresh` | Rotate the refresh token. |
| POST | `/auth/logout` | Revoke a refresh token. |
| GET | `/auth/me` | Authenticated user. |

### Users
| Method | Path | Notes |
|---|---|---|
| GET | `/users/me` | |
| PATCH | `/users/me` | Profile edit. |
| POST | `/users/me/avatar-upload` | Presigned PUT URL. |
| GET, POST | `/users/me/push-tokens` | Register / list device push tokens. |
| DELETE | `/users/me/push-tokens/{id}` | Revoke a device. |

### Reference data
`GET /reference/{cities,vibes,drinks,races}` — static lookup tables.

### Bars
`GET /bars` (search + filter + near-me) · `GET /bars/{id}` · `GET /bars/favorites` ·
`POST/DELETE /bars/{id}/favorite` · `PUT/DELETE /bars/{id}/review`

### Quiz
`GET /quiz/questions` · `POST /quiz/submit` · `GET /quiz/me`

### Friends + groups
`GET /friends` · `*/friends/requests/...` · `/friend-groups` with member endpoints.

### Raids
`GET/POST /raids` · `GET/PATCH /raids/{id}` · `POST /raids/{id}/cancel` ·
`POST /raids/{id}/rsvp`

### Notifications
`GET /notifications` (with `unread_only`) · `/unread-count` · `/{id}/read` · `/read-all`

### Checks (receipts + split room + dice)
`POST /checks` (OCR triggered) · `GET /checks` · `GET /checks/{id}` ·
`POST /checks/{id}/{invite,join,leave,ready,unready}` ·
`PUT/DELETE /checks/{id}/items/{item_id}/assignments[/{participant_id}]` ·
`POST /checks/{id}/dice/propose` · `POST /checks/{id}/dice/{proposal_id}/vote` ·
`GET /checks/_/kind-soul/leaderboard`

### Achievements
`GET /achievements` · `/achievements/me` · `/achievements/me/points`

### Chat
`GET/POST /chat/conversations` · `/chat/conversations/{id}` ·
`GET/POST /chat/conversations/{id}/messages` · `PATCH/DELETE /chat/messages/{id}` ·
`POST /chat/messages/{id}/reactions` · `POST /chat/conversations/{id}/read` ·
`GET /chat/presence`

### Tavern Tales (D&D AI DM)
`GET /tavern/classes` · `GET/POST/PATCH/DELETE /tavern/characters[/{id}]` ·
`POST /tavern/sessions` · `GET /tavern/characters/{id}/sessions` ·
`GET /tavern/sessions/{id}/messages` ·
`POST /tavern/sessions/{id}/{turn,roll,end}` · `GET /tavern/quota`

### Realtime
`WS /ws?token=<jwt>` — JWT-authenticated WebSocket. Receives:
`notification.new`, `message.new`, `message.updated`, `message.deleted`,
`reaction.toggled`, `read.advanced`, `participants.changed`,
`participant.joined/left/ready/unready`, `assignment.updated/removed`,
`dice.proposal.created/declined`, `dice.completed`, `presence.self`.

Interactive docs: <http://localhost:8000/docs>.

## External services

`app/services/` holds adapters with a stub + a live implementation each, picked
by `app/services/registry.py` based on `.env`:

| Adapter | Live | Stub |
|---|---|---|
| OCR (`ocr.py`) | OpenAI Vision | Hardcoded Lviv beer-bar receipt |
| Storage (`storage.py`) | S3 / R2 presigned PUT | `file://` path in tempdir |
| Push (`push.py`) | Expo Push API | Log only |
| LLM (`llm.py`) | OpenAI Chat (streaming) | Canned reply |

Setting `OPENAI_API_KEY` (or `S3_BUCKET` + creds) flips the relevant adapter
to live mode at startup. No code changes needed.

## Dev workflow

```bash
uv run ruff check .                # lint
uv run ruff format .               # format
uv run mypy app                    # type-check
uv run pytest                      # tests (none yet)
uv run alembic revision -m "msg"   # new migration
uv run alembic upgrade head        # apply migrations
```
