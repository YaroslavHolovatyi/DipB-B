# WP7 — Test Coverage & Demo Build: What's Left

The authorable part is done: backend tests for the new modules
(`test_raids.py`, `test_parties.py`, `test_checks_event.py`) are written and
compile clean. Everything below needs your machine, a device, or credentials,
so it can't be done from here. **Done when: green tests, the app running on a
phone, and an installable artifact.**

---

## 1. Run the backend suite (green tests)

These can't execute in the sandbox (no Postgres/Redis/venv). On your Debian box:

```bash
cd backend
docker compose up -d                # Postgres+PostGIS + Redis
uv run alembic upgrade head         # apply schema incl. 0006_event_check_link
uv run pytest -v                    # full suite
```

What to expect:

- The suite **auto-skips** if Postgres/Redis aren't reachable — if you see
  skips, the containers aren't up or the DB URL is wrong.
- New coverage: raid no-show drops rating by 25, attended credits +1,
  `complete` auto-no-shows unverified RSVPs, party create/join/leave/cancel,
  and `POST /checks/from-event` attendee seeding + duplicate/permission guards.
- The event-check tests rely on the **OCR stub**. Keep `OPENAI_API_KEY` empty
  in the test env, or those tests will try a live Vision call against a fake
  image URL and fail.

If anything goes red, that's a real bug to fix before the demo — report the
failing test and I'll dig in.

## 2. Reconcile every RTK Query endpoint with a live route

Before trusting the app on a device, confirm the mobile API layer matches the
backend. Quick sweep:

- Diff each `mobile/api/*.ts` `injectEndpoints` URL/method against the FastAPI
  routers (`/raids`, `/parties`, `/checks`, `/users/me/*`, `/auth`, `/chat`).
- Confirm tag invalidation lines up (e.g. `from-event` invalidates `CheckList`,
  `verify` should refresh `UserStats`).
- Watch for trailing-slash and query-param mismatches — the usual silent 404s.

I can generate a route-vs-endpoint comparison table if you want a checklist.

## 3. Run the app on a phone (runtime verification)

```bash
cd mobile
npm install
npx expo start                      # scan QR with Expo Go
```

Smoke path to walk through manually:

1. Sign up / log in, set profile (bio + interests), see stats card.
2. Create a raid → RSVP from a second account → checkpoint → verify → see
   rating move on the profile screen.
3. Create a party → join from second account → see roster.
4. From a completed raid, tap **Split the shared bill** → confirm the split
   room opens seeded with attendees.
5. Send a chat message between two accounts.

Point `EXPO_PUBLIC_API_URL` (or your env equivalent) at your machine's LAN IP,
not `localhost`, so the phone can reach the backend.

## 4. Live OpenAI smoke test (OCR + Tavern Tales)

With a funded key set in the backend `.env`:

```bash
OPENAI_API_KEY=sk-...               # enables OpenAiOcrService + GPT-4o
```

- Upload a real receipt photo via `POST /checks/upload-url` → PUT → `POST
  /checks` and confirm the parsed line items look sane.
- Trigger one Tavern Tales (GPT-4o) generation and confirm it returns.
- Keep this **out of the pytest env** (see step 1).

## 5. EAS build → installable artifact

```bash
npm install -g eas-cli
eas login
cd mobile
eas build:configure                 # creates/updates eas.json if needed
eas build --profile preview --platform android   # → installable .apk
# iOS (needs Apple credentials):
eas build --profile preview --platform ios
```

- Use a **`preview` profile** with `"distribution": "internal"` so Android
  yields a directly-installable `.apk` (the default `production` profile makes
  an `.aab` you can't sideload for a demo).
- Make sure `EXPO_PUBLIC_API_URL` in the build profile points at a reachable
  backend (a tunnel or deployed host — not localhost — if you demo off-network).
- Download the artifact from the EAS build page; that's your diploma demo
  deliverable.

---

## Suggested order

1. Backend tests green (step 1) — fastest signal, catches regressions.
2. Endpoint reconciliation (step 2) — cheap, prevents device-time surprises.
3. App on a phone via Expo Go (step 3) — validates the real flows.
4. Live OpenAI keys (step 4) — only once the flows work on stubs.
5. EAS build (step 5) — last, once everything behaves.

## Open question from WP6

Parties have no attendance verification, so rating is only scored on the raid
path. If you want parties to affect reputation too, the clean addition is a
host **"close party → credit joined members"** action (mirrors raid
`complete`). Say the word and I'll spec + build it.
