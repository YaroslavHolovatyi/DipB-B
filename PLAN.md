# Build Plan — Tavern Tales

A location-based social app: users discover real-world places ("taverns") on a PostGIS-powered map, scan receipts to log and verify visits, and GPT-4o turns each visit into a short fantasy "tavern tale." Backend is FastAPI; the app is Expo (React Native).

This plan is a phased roadmap from a clean Debian machine to a demoable build. Each phase has a goal, concrete tasks, and a "done when" check so progress is unambiguous.

---

## Architecture at a glance

```
                 ┌──────────────────────────┐
   Expo app  ──► │  FastAPI  (app/api)       │ ──► PostgreSQL + PostGIS
 (mobile/src)    │  services / schemas / db  │ ──► Redis (cache, jobs)
                 └────────────┬─────────────┘
                              │
                      OpenAI API
              ┌───────────────┴───────────────┐
        Vision (receipt OCR)        GPT-4o ("Tavern Tales")
```

Core entities (as implemented in `database/schema.sql`):

- **User** (`users`) — account, profile, chosen D&D race, home city.
- **City / Bar** (`cities`, `bars`) — the real-world catalog; both carry a `GEOGRAPHY(POINT, 4326)` location with GiST indexes. "Bar" is the app's "Place".
- **Check / Receipt** (`checks`, `check_items`) — a logged visit + its OCR'd bill. `checks.ocr_payload` (JSONB) holds the raw OpenAI Vision response; `check_items` are the parsed line items.
- **Split** (`check_participants`, `check_item_assignments`, `dice_proposals`, `dice_proposal_votes`) — the bill-splitting flow, including the "d20 dice / choose one to pay for all" consent mechanic.
- **Tavern Tales** (`dnd_*`: `dnd_characters`, `dnd_sessions`, `dnd_messages`, `dnd_usage_quota`) — the single-player GPT-4o AI Dungeon Master experience.
- **Social & engagement** (`user_friends`, `friend_requests`, `friend_groups`, `raids`, `conversations`/`messages`, `quiz_*`, `achievements`/`user_achievements`, `notifications`, `push_tokens`) — friends, group "raids" to bars, chat, the race quiz, achievements, and notifications.

> Note: the schema is richer than a minimal Place/Visit/Receipt/Tale model. The mapping is: Place→`bars`, Visit/Receipt→`checks`+`check_items`, Tale→the `dnd_*` tables. Later phases reference these real table names.

---

## Phase 0 — Local environment (Debian)

**Goal:** every tool from the project spec installed and verified.

- System packages: `build-essential`, `git`, `libssl-dev`, `pkg-config`, `curl`.
- Docker Engine + Docker Compose plugin; add user to the `docker` group.
- Python 3.12 + [`uv`](https://github.com/astral-sh/uv) for env + dependency management.
- PostgreSQL client (`psql`) for direct DB inspection.
- Node.js 22 LTS via `nvm`.
- `npm i -g eas-cli` and the Expo tooling; install **Expo Go** on your phone.
- VS Code with Python, ESLint, Prettier extensions.
- GitHub CLI / SSH key wired to the repo.
- OpenAI account + API key (store in `.env`, never commit).
- Optional: DBeaver (DB GUI), HTTPie (API testing), direnv (auto-load `.env`).

**Done when:** `docker compose version`, `uv --version`, `psql --version`, `node -v` (v22), `eas --version`, and `gh auth status` all succeed.

---

## Phase 1 — Repo, infra & migrations

**Goal:** services run in Docker and the DB schema is version-controlled.

- Confirm `docker-compose.yml` brings up **PostGIS** and **Redis**; pin image versions.
- `.env.example` with every required var (DB URL, Redis URL, `OPENAI_API_KEY`, JWT secret); real `.env` git-ignored.
- Backend env via `uv` (`pyproject.toml`/`requirements.txt`), pinned deps.
- Add **Alembic** migrations; enable the PostGIS extension in the first migration. *(Done: `0001_baseline` applies `database/schema.sql` verbatim, which enables `postgis`, `citext`, `pg_trgm`, `uuid-ossp`.)*
- Define SQLAlchemy models per feature module in `backend/app/<feature>/models.py` (auth, users, bars, checks, friends, raids, quiz, chat, achievements, notifications, tavern_tales, reference). Geo columns (`cities`, `bars`, `raids`) use GeoAlchemy2 `Geography(Point, 4326)`. *(Done.)*

**Done when:** `docker compose up` is healthy, `alembic upgrade head` creates all tables, and `psql` shows the PostGIS extension and the `bars` geo column. Verify locally:

```bash
docker compose up -d
cd backend && uv run alembic upgrade head
psql postgresql://app:app@localhost:5432/beer_and_beverages -c '\dx' -c '\d bars'
```

---

## Phase 2 — Backend foundation (auth + core API)

**Goal:** a running FastAPI service with auth and CRUD.

- App wiring in `app/main.py`, settings in `app/core/config.py`, DB session in `app/db`.
- Auth: registration, login, JWT issue/verify, password hashing; `get_current_user` dependency.
- Pydantic schemas in `app/schemas` for each entity.
- Routers in `app/api`: users/auth, places, visits.
- **Geo query**: "places near me" using PostGIS `ST_DWithin` ordered by distance (lat/lng/radius params).
- Health check + OpenAPI docs at `/docs`.

**Done when:** you can register, log in, create a place, and query nearby places via HTTPie/`/docs`.

---

## Phase 3 — Receipt OCR pipeline

**Goal:** photo of a receipt → structured data attached to a visit.

- Reuse/refine the existing scaffolding (`receipt_ocr_schema.py`, `receipt_api_endpoints.py`, `receipt_processing_workflow.py`) into `app/services`.
- Upload endpoint: accept image, store it (local/object storage), create a Receipt row.
- Call **OpenAI Vision** to extract merchant, date, total, line items into the defined schema.
- Process async via a Redis-backed job/queue; expose status so the app can poll.
- Validate/normalize output (currency, totals); handle low-confidence/failed OCR gracefully.
- Optional: match the receipt's merchant/location to a nearby Place to auto-confirm the visit.

**Done when:** uploading a sample receipt returns structured fields and links to a Visit, with a clear status while processing.

---

## Phase 4 — Tavern Tales (GPT-4o)

**Goal:** turn a visit into a short fantasy narrative.

- `app/services` Tale generator: prompt GPT-4o with place name, visit context, and receipt highlights.
- Prompt design + guardrails (length, tone, no hallucinated facts about the user); store the result as a Tale.
- Endpoint to generate/fetch the tale for a visit; cache in Redis to avoid regenerating.
- Optional flourishes: XP/level or "quest" framing per visit; shareable tale card.

**Done when:** a completed visit (with receipt) produces a coherent, themed tale persisted and retrievable via the API.

---

## Phase 5 — Mobile app (Expo)

**Goal:** end-to-end flow on a real phone via Expo Go.

- API client + token storage in `mobile/src/api` and `mobile/src/services`; state in `mobile/src/store`.
- Navigation (`mobile/src/navigation`) + theme (`mobile/src/theme`).
- Screens: Auth (login/register), **Map** of nearby places (PostGIS results), Place detail, Capture receipt (camera), Visit/Tale view, Profile.
- Wire the full loop: open map → pick place → snap receipt → see OCR result → read the generated tale.
- Loading/empty/error states; location permission handling.

**Done when:** the complete discover → scan → tale loop runs on your phone over the Expo Go QR code.

---

## Phase 6 — Hardening & polish

**Goal:** reliable and presentable.

- Backend tests (pytest) for auth, geo queries, OCR parsing, tale generation (mock OpenAI).
- Input validation, rate limits on OpenAI-backed endpoints, sensible error responses.
- Logging + basic observability; cost guards on OpenAI calls.
- Seed script with demo places/receipts for a clean demo run.
- Tidy README + the existing SETUP docs so a fresh clone is reproducible.

**Done when:** tests pass in CI/local, and a fresh clone reaches a working demo using the seed data.

---

## Phase 7 — Builds & demo

**Goal:** an installable artifact and a rehearsed demo.

- Configure `eas.json`; build an `.apk` (and `.ipa` if needed) with **EAS**.
- Point the build at a reachable backend (tunnel or deployed).
- Final pass on diagrams in `diagrams/` to match the shipped system.
- Rehearse the demo path and prep fallback screenshots/recording.

**Done when:** the `.apk` installs and runs the core loop against the backend, and the demo script is rehearsed.

---

## Suggested order & dependencies

Phase 0 → 1 → 2 are sequential. Phase 3 and 4 both depend on 2 (3 before 4, since tales use receipt data). Phase 5 can start against stubbed endpoints once 2 lands, then integrate 3/4. Phases 6–7 come last.

## Immediate next steps

1. Verify Phase 0 tooling, then `docker compose up` and confirm PostGIS + Redis are healthy.
2. Add Alembic and write the first migration (enable PostGIS, create core tables).
3. Stand up auth + the "nearby places" geo endpoint — the backbone everything else hangs off.
