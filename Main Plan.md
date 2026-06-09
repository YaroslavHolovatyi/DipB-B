# Tavern Tales — Work Done So Far

**Project:** Tavern Tales (codebase name *Beer & Beverages*) — a location-based social app where users discover real-world places ("taverns") on a PostGIS map, scan receipts to log and verify visits, split bills, and have GPT-4o turn visits into fantasy "tavern tales."

**Stack:** FastAPI (Python 3.12) backend · PostgreSQL + PostGIS · Redis · Expo / React Native (TypeScript) mobile app · OpenAI (Vision OCR + GPT-4o).

**Status as of 2026-06-08:** Backend and mobile frontend are both structurally complete. Mobile app type-checks with zero errors; backend has a working test suite and a versioned database schema.

---

## 1. Backend (FastAPI) — ~8,900 lines

Modular FastAPI service organized by domain. Each domain follows a consistent `models / schemas / service / router` layout. **16 routers** are wired into the app, exposing roughly **90+ REST endpoints** plus a WebSocket gateway.

### Implemented modules

| Module | Endpoints | What it does |
|---|---|---|
| `health` | 3 | Liveness/readiness probes |
| `auth` | 5 | Signup, login, JWT refresh, logout, refresh-token rotation |
| `api/venues` | 5 | Venue (place) catalog |
| `users` | 6 | Profile, profile edit, user lookup |
| `reference` | 5 | Reference data: cities, drinks, vibes, D&D races/classes |
| `bars` | 7 | Bar discovery, detail, favorites, reviews, photos, vibes |
| `quiz` | 3 | "Race" quiz that assigns a D&D race to the user |
| `friends` | 7 | Friend requests, friends list, friend groups |
| `raids` | 6 | Group outings ("raids") to bars |
| `notifications` | 4 | In-app notifications + push token registration |
| `checks` | 14 | Receipt/visit logging, OCR payload, bill splitting, item assignment, dice-based "who pays" mechanic |
| `achievements` | 3 | Achievements and user achievement progress |
| `chat` | 10 | Conversations, messages, reactions, presence |
| `tavern_tales` | 13 | Single-player GPT-4o AI Dungeon Master: characters, sessions, messages, usage quota |
| `realtime` | 1 (WS) | WebSocket gateway for chat/presence/live updates |

### Core infrastructure
- **`core/`** — settings/config, async DB engine, dependency injection, Redis client, security (JWT, password hashing).
- **`realtime/`** — WebSocket connection manager + Redis pub/sub for fan-out across workers.
- **`services/`** — OpenAI **LLM** (Tavern Tales), **OCR** (receipt vision), **receipt OCR service**, **push** notifications, **storage**, and a service **registry**.
- **`shared/`** — shared exceptions and pagination helpers.

### Data model — 45 tables
PostGIS `GEOGRAPHY(POINT,4326)` with GiST indexes on cities/bars for geospatial queries. Domains covered:
- **Accounts & places:** `users`, `cities`, `bars`, `bar_favorites`, `bar_photos`, `bar_reviews`, `bar_vibes`, `vibes`, `drinks`.
- **Visits & receipts:** `checks`, `check_items`, `check_participants`, `check_item_assignments`, `dice_proposals`, `dice_proposal_votes` (the d20 "one pays for all" consent flow).
- **Tavern Tales (AI DM):** `dnd_characters`, `dnd_sessions`, `dnd_messages`, `dnd_class_info`, `dnd_usage_quota`.
- **Social & engagement:** `user_friends`, `friend_requests`, `friend_groups`, `friend_group_members`, `raids`, `raid_participants`, `conversations`, `conversation_participants`, `messages`, `message_reactions`, `quiz_questions`, `quiz_answers`, `quiz_answer_races`, `user_quiz_results`, `races`, `race_drinks`, `race_vibes`, `quiz_answer_races`, `achievements`, `user_achievements`, `kind_soul_events`, `notifications`, `push_tokens`, `user_presence`, `refresh_tokens`.

### Migrations & tests
- **Alembic** migrations with a baseline migration (`0001_baseline`).
- **Pytest** suite (`test_auth`, `test_bars`, `test_chat`, `test_health`, `test_reference`) with shared fixtures in `conftest.py`.

---

## 2. Mobile app (Expo / React Native) — ~8,300 lines

Expo SDK 54, React 19, React Native 0.81, **expo-router** file-based navigation, **Redux Toolkit + RTK Query** for state and API, **Tamagui** for theming. **Type-checks cleanly (`tsc --noEmit`, 0 errors)**, dependencies installed, no stub/TODO markers in screens.

### Screens (22 routes)
- **Auth flow:** landing, sign-in, sign-up.
- **Tab navigator (5 tabs):** Home, Bars, Map, Friends, Profile.
- **Feature screens:** bar detail, chat thread, checks (list/new/detail), raids (detail/new), quiz, tavern (list + session), notifications, profile edit.

### API layer (14 RTK Query slices)
`auth`, `users`, `bars`, `checks`, `friends`, `chat`, `raids`, `tavern`, `quiz`, `achievements`, `notifications`, `references`, plus shared `baseQuery` and `types`. These map 1:1 to the backend domains.

### Supporting code
- **State:** Redux store + auth slice.
- **lib:** runtime config, secure token storage (`expo-secure-store`), WebSocket client, push-notification setup.
- **Reusable components:** auth inputs; home cards (activity item, raid card, tavern card, section header); profile (achievement badge, leaderboard row).
- **Theming:** Tamagui config, color tokens, style helpers; Google Fonts (Fraunces, Jakarta Sans, JetBrains Mono).
- **Native integrations wired:** location, image picker (receipt capture), notifications, haptics, linear-gradient, webview, gesture-handler, reanimated.

---

## 3. Infrastructure & project assets
- **`docker-compose.yml`** — PostGIS + Redis containers.
- **Database:** `database/schema.sql` + seed data in `database/seeds/`.
- **Diagrams:** receipt processing sequence (SVG) and workflow diagrams.
- **Docs:** `PLAN.md` (phased roadmap), `PROJECT.md`/`PROJECT.html` (full spec), `SETUP.md`/`SETUP-DB.md`, `HOW_TO_RUN_AND_TEST.md`, `DESIGN_PROMPT.md`, Gemini-generated design mockups.
- **Thesis:** `Диплом_Головатий_31_05.docx` and `Thesis_Holovatyi_abstract.docx`.

---

## 4. Headline features delivered
1. **Auth** — JWT access/refresh with rotation, secure mobile token storage.
2. **Geospatial place discovery** — PostGIS-backed bar/city catalog with map and list views.
3. **Receipt scanning & visit logging** — OpenAI Vision OCR into structured line items.
4. **Bill splitting** — participants, per-item assignment, and the d20 dice "one pays for all" consent mechanic.
5. **Tavern Tales** — GPT-4o single-player AI Dungeon Master with characters, sessions, and usage quotas.
6. **Social graph** — friends, friend requests, friend groups, group "raids."
7. **Real-time chat** — conversations, messages, reactions, presence over WebSocket + Redis pub/sub.
8. **Gamification** — D&D race quiz, achievements, leaderboards.
9. **Notifications** — in-app feed + push token registration/delivery.

---

## 5. Not yet done / next steps
- **Runtime verification** of the mobile app on a device/emulator (currently type-safe but not launch-tested here).
- **End-to-end check** that every mobile RTK Query endpoint matches a live backend route.
- **Broader backend test coverage** — current suite covers auth, bars, chat, health, reference; checks/tavern/raids/notifications endpoints are untested.
- **EAS build** of an installable `.apk`/`.ipa` for the demo.
- **Real OpenAI keys + live OCR/LLM integration testing.**

## 6. Description for this application
So what do we need this app to do - this is an application for social interaction between different people.
first of all the user enters the pplication and can login or sign up
after signup he has to pass a small quiz in order the application to know him better (make his race depending on the answers form the quiz)
when on the main page he sees this set up:
header - there is a logo of the application (I will add it myself, and all the ) in the middle and user logo on the right of the header in order to go to the user page
than the main part - there should be several different section - popular bars, last bars visited by friends and with the rating of those bars by friends only! raids near you and people searching for party members
what is raid - raid is special occasion created by users (can be open for all and open for friends only) where there is a theme of the raid (for example - play tabletop games with interested people) and people can 
click the button "join the raid" in order to show if they will attend this event, you can not visit two different raids at the same time! when you join the raid 0 you need to visit it and the raid leader (the host of the event) has to check if you have attended the raid or not. There should be the button - checkpoint reached in order to show that the user is already at the event.
when creating raid - the host should choose the location (bar of different type of fast food establishement), write the theme of the event, choose the time of the event, check the users that ware at the event, and choose what is the maximum number of people for the event. if the event finishes much quicker then it was said - the host of the event has to have an option to baort the event or finish it.
What is people searching for party memebers - if user wants to meet other users he can create a party, when creating a party the user can send notification to other users, friends from the friends list and make party open for the other users to enter the party. in order for the user to create or visit this part of the application he has to write small about himself and choose his interest (these will be interests chips like hiking, tabletop games, dnd and so on), in order to match the party. if the party is full the app should show the message "the party you are trying to enter is already full"
and there also should be the footer in the footer there should be 5 positions 1) search bar/fast food etc, 2) social (where already created raids and parties are they should be shown like cards and there should be 3 types of notifications shown on those cards - some friends are attending, 'only friends' of the user, and nobody you know is attending) 3) create party/raid 4) messages 5) ai dnd game

  when party or raid over there should be a step where host will take the photo of the check, parse it with ai and make the payroll foe all the users who attended the event, all the other users should get notifications for the parsed into checkbox page of the check and choose the position they ordered and quantity of those positions ordered by them.

  all the users have to have social rating - for example if the user did not attent the event he subscribed to attend - shoud get him demoted and dropped the rating for some points, the user should also have statistics of the events he attended, events he diched and maybe some other stuff  
 
   
