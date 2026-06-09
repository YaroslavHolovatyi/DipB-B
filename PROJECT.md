# Beer & Beverages — Project Documentation

A mobile rebuild of the diploma project "Довідка пабів м. Львів" (Lviv pubs directory) on a new technology stack. The original was an Angular + Spring Boot + MySQL web SPA; this version is a cross-platform mobile app with a Python backend and a PostgreSQL database, and it adds real-time multi-device features (chat and live activity) so the system can be demonstrated convincingly from two phones at once.

## Vision

Beer & Beverages is a social mobile app that combines a directory of bars and pubs with light gamification and group-coordination features. A user opens the app, finds bars near them, marks favorites, plans a "raid" (a planned visit), brings friends along through a "Party for Dungeon" group, chats with them in real time, splits the bill from a photo of the receipt, and lets a D20 dice roll decide who pays for everyone — generating a "Добра Душа" (Kind Soul) score that feeds a leaderboard. Along the way the user takes a quiz that assigns them a fantasy race, unlocks achievements, and receives notifications about friends' activity. The fantasy/tavern theme of the original product is preserved throughout — bars are "taverns", group plans are "raids", friend groups are "parties".

## Scope changes from the original

The original project, as described in the coursework documentation, was a desktop-first web app. The new version pivots to mobile and adds a real-time layer. Most features carry over with parity; a handful are reframed for mobile or expanded.

The receipt-split flow becomes camera-driven instead of file-upload. "Raids near you" uses real device geolocation instead of a city dropdown. Notifications are now both in-app and push (Expo / APNs / FCM). The biggest functional addition is a chat module — direct messages and group chats — so two users can communicate inside the app, with messages delivered live over a WebSocket. Activity that other users care about (friend requests, raid RSVPs, new check shares) is also pushed live over the same socket so the other device updates without polling.

## Technology stack

The frontend is React Native on Expo, written in TypeScript. Navigation uses Expo Router (file-based routing). Styling and components come from Tamagui, which gives a single themeable component library and good performance on native. Server state is handled by Redux Toolkit with RTK Query — this stays close to the NgRx pattern from the original project, gives us a familiar `slice + selectors + queries` story, and provides automatic cache invalidation and re-fetch. WebSocket live events are bridged into the Redux store so RTK Query caches stay fresh without manual refetches.

The backend is FastAPI on Python 3.12, served by Uvicorn behind a process manager. The ORM is SQLAlchemy 2.0 with the async API and `asyncpg` driver; schema migrations are managed by Alembic. Authentication uses short-lived JWT access tokens (signed with HS256) and rotating refresh tokens stored as hashes. Password hashing is Argon2 via `passlib`. Real-time messaging uses FastAPI's native WebSocket support, with a small connection manager and Redis Pub/Sub fan-out so the system works correctly when multiple Uvicorn workers are running. Receipt OCR is handled by calling OpenAI's vision API on the server; raw payloads are stored as JSONB for audit and re-parse.

The database is PostgreSQL 16 with the PostGIS, citext, pg_trgm, and uuid-ossp extensions. PostGIS handles geo queries for "bars near me" and "raids near me". JSONB columns store OCR payloads, push-notification data, achievement requirements, and quiz score breakdowns. A `tsvector` column with a GIN index powers full-text search across the bar catalog. The full schema is in `database/schema.sql` with a detailed overview in `database/SCHEMA.md`.

Supporting infrastructure is Redis (for Pub/Sub between WebSocket workers and as a short-TTL cache for hot queries), S3-compatible object storage (e.g. Cloudflare R2 or AWS S3) for user-uploaded images — avatars, receipt photos, bar photos — and Expo Push for delivering notifications to devices that aren't currently connected over WebSocket.

| Layer | Choice | Why this and not something else |
|---|---|---|
| Mobile UI | React Native + Expo | Single codebase for iOS and Android; Expo's managed workflow ships faster than bare RN for a solo diploma project; works on a real device over LAN out of the box, which matters for the two-phone demo. |
| Navigation | Expo Router | File-based routing matches modern React conventions and avoids a separate route config. |
| Component library | Tamagui | Performant, themeable, native + web. Spiritually fills the Angular Material slot from the old project. |
| Client state | Redux Toolkit + RTK Query | Familiar to anyone who used the original NgRx setup; RTK Query gives automatic cache + invalidation, which keeps the WebSocket-driven live updates simple. |
| Real-time client | Native browser WebSocket | First-class in React Native; no Socket.IO dependency unless we need rooms semantics. |
| API | FastAPI (Python 3.12) | Async, fast, automatic OpenAPI schema generation, native WebSocket support, big community. |
| ORM | SQLAlchemy 2.0 + asyncpg | First-class async, mature, plays well with FastAPI's dependency injection. |
| Migrations | Alembic | Pairs with SQLAlchemy; revision-based, reviewable. |
| Auth | JWT (access + refresh) | Stateless access tokens, rotating refresh tokens stored hashed. |
| Realtime backplane | Redis Pub/Sub | Lets multiple Uvicorn workers fan out the same event to all connected clients. |
| Storage | PostgreSQL 16 + PostGIS | Heavy relational data + geo + JSONB + FTS in one engine. |
| Object storage | S3-compatible (R2 or S3) | Cheap, signed-URL uploads from the phone, decoupled from the DB. |
| Push | Expo Push Notifications | One API for both iOS and Android, no native cert juggling during the diploma. |
| LLM (AI DM) | OpenAI GPT-4o (streaming) | Strong creative writing, function-calling for structured dice / state updates, mature SSE streaming SDK. Used by the Tavern Tales feature only; never exposed to the client. |

## High-level architecture

The system is a classic client-server architecture with a real-time side-channel. Both phones run the same Expo app, authenticate against the FastAPI server, and hold an open WebSocket connection for the duration of the session. REST endpoints are used for everything that's a normal CRUD operation: list bars, fetch a profile, post a review, create a raid, upload a receipt for OCR. The WebSocket carries only ephemeral or push-style traffic: incoming messages, typing indicators, presence updates, and "live activity" events such as "your friend just RSVP'd to a raid" or "a new check was shared with you."

Data flow for a chat message from device D1 to device D2 looks like this. D1 sends an HTTP POST to `/api/conversations/{id}/messages` with the message body. The handler validates the sender is a participant, inserts a row into `messages`, which fires a trigger that updates `conversations.last_message_at`. The handler then publishes an event onto Redis Pub/Sub on a channel keyed by conversation id. Every Uvicorn worker subscribed to that channel — whichever worker happens to host D2's WebSocket — receives the event and writes the message JSON to D2's open socket. D2's React Native code receives the frame, dispatches an action that inserts the message into the RTK Query cache for that conversation, and the chat screen re-renders. If D2 is offline (no WebSocket), the same publish step queues a push notification through Expo Push instead, so D2's device wakes up with a banner. When D2 reopens the app, the conversation is already up to date from the next `getMessages` query, which the cache invalidation forces.

The same pattern applies to non-chat live updates. When D1 marks a bar as a favorite, the REST handler publishes a `favorite.added` event to a user-scoped channel. Any other device the user has logged in on receives the event and patches the favorites cache. This avoids stale UIs across devices without resorting to aggressive polling.

```
┌──────────────┐   HTTP/JSON   ┌──────────────┐   SQL   ┌──────────────┐
│  Expo app D1 │──────────────▶│  FastAPI     │────────▶│ PostgreSQL   │
│  (RN)        │◀──WebSocket───│  (Uvicorn)   │         │ + PostGIS    │
└──────────────┘               │              │         └──────────────┘
                               │              │   pub/sub   ┌────────┐
┌──────────────┐   HTTP/JSON   │              │◀───────────▶│ Redis  │
│  Expo app D2 │──────────────▶│              │             └────────┘
│  (RN)        │◀──WebSocket───│              │
└──────────────┘               └──────────────┘   ┌────────┐   ┌──────────────┐
                                                  │ S3/R2  │   │ Expo Push    │
                                                  └────────┘   └──────────────┘
```

## Feature catalogue

A user signs up with first name, email, username, and password, and picks a main city. The server creates the account, hashes the password with Argon2, and returns an access token plus a refresh token. The mobile app stores the refresh token in `expo-secure-store` (which writes to iOS Keychain or Android EncryptedSharedPreferences) and keeps the access token in memory. On a 401 the client transparently calls `/auth/refresh` to rotate tokens; if that fails, the user is sent to the login screen.

Once logged in, the user lands on a tab navigator with four primary tabs: Home, Bars, Friends, Profile. Home shows recommended bars, upcoming raids the user is going to, and a feed of friends' recent activity. Bars opens the catalog, where the user can search by name (full-text), filter by city, price category, and rating, and tap into a detail page with photos, work hours, vibes, reviews, and an "Add to favorites" heart. From the detail page the user can also start a raid at that bar. Friends opens the social hub: friends list, incoming friend requests, friend groups ("parties"), and the chat inbox. Profile shows the user's avatar, race, achievements, favorite bars, check history, and an edit form for personal information.

Receipt splitting works as a collaborative "split room" rather than a single-user form. The flow is described in detail in the next section because it is the most multi-device part of the app.

Quiz works as a one-shot screen accessible from the Profile tab. The user answers each question, the server sums per-race scores from `quiz_answer_races`, picks the race with the highest score (with a deterministic tiebreaker), updates `users.race_id`, and inserts a row into `user_quiz_results` with the full breakdown for transparency. Races affect the visual theme on the user's profile, sort their recommended drinks, and gate certain race-specific achievements.

Raids are events. Any user can create a raid at a bar (or freeform location), set a scheduled time, optionally cap participants, and invite friends. Invitees see the raid in their Home feed and in the Notifications screen; they can RSVP "going", "maybe", or "declined." A raid that's about to start triggers a push notification. The "Raids near you" surface on the Home tab queries `raids` by `ST_DWithin(location, $user_location, $radius_m)` and filters by scheduled time and status.

Chat supports both direct messages between two friends and group chats. A direct chat is created lazily the first time one user messages another — the server looks for an existing `conversations` row of type `direct` with exactly those two participants, and creates one if missing. A group chat can either be ad-hoc (no `friend_group_id`) or tied to a `friend_group` (so editing the group's membership automatically reshapes the chat's participants). Messages can carry text, image attachments (stored on S3, referenced as JSONB), and an optional `reply_to_id`. Reactions are a simple `(message_id, user_id, emoji)` composite primary key. Read receipts are computed from `conversation_participants.last_read_at` versus message `created_at`.

Achievements are coded as rows in the `achievements` table with a JSONB `requirement` describing the unlock condition (for example `{"type": "check_count", "threshold": 10}`). When a relevant event happens — a receipt is created, a quiz is finished, a raid completes — the backend evaluates which achievements apply and either bumps `user_achievements.progress` or inserts a fully-awarded row. Race-specific achievements (`achievements.race_id IS NOT NULL`) only count for users of that race.

Notifications cover everything that needs to surface even when the user isn't on the relevant screen: friend requests, raid invites, raid reminders, achievement unlocks, "you were chosen to pay" events, and system messages. They live in the `notifications` table with a JSONB `data` payload, a `type` enum that routes display logic, and a partial index on `read_at IS NULL` for the badge count. Chat messages do *not* create notification rows on the server (that would create heavy churn); instead, when a message arrives and the recipient is offline, the server sends a single Expo Push notification with a "tap to open chat" deep link.

## Collaborative split room

The split room is the multi-device flow that the rest of the app is designed around. It starts when a user — the "host" — takes a photo of a receipt on their phone. The image goes through a presigned upload to S3, then the URL is posted to `POST /api/checks`. The server stores the header row in `checks`, calls the OpenAI Vision API to extract line items, persists the raw response in `checks.ocr_payload` for audit, and writes a row per item into `check_items`. The host is then redirected into the split-room screen for that check.

From inside the room, the host invites participants. Each invitee is either an existing friend (registered user — selected from a list of party members), or a freeform guest (the host types a display name). For each registered invitee the server inserts a `check_participants` row with `status='invited'`, a `notifications` row of type `check_invite`, and a push notification through Expo Push so the device wakes up even if the app is closed. Guests are inserted with `status='joined'` directly because they don't have an account to vote with.

When an invitee taps the notification, the app opens the same split-room screen, the server flips their `check_participants.status` to `joined`, fills in `joined_at`, and broadcasts a `participant.joined` event on the `check:{id}` WebSocket channel. Every participant currently in the room sees the new person appear in the participant list in real time.

Inside the room every participant sees the same item list and the same participant list. To claim an item, a participant taps the row and selects how many units they had — one beer out of two, half of the appetiser, all of their cocktail. The action goes through `PUT /api/checks/{id}/items/{itemId}/assignments` with a body containing the calling user's participant id and a quantity. The server upserts a row into `check_item_assignments`, computes the amount as `quantity × unit_price`, and re-computes each participant's running subtotal. It then publishes two events to `check:{id}`: an `assignment.updated` event with the changed row, and a `totals.updated` event with the new per-participant subtotals. Every device updates its UI in the same frame — the marked item shows the claimant's avatar/colour chip beside it, and the personal subtotal at the top of every participant's screen ticks up.

When a participant has marked all the items they had during the night, they tap "Ready". The server sets their `status='ready'` and `ready_at=now()`, broadcasts `participant.ready`, and shows the participant a read-only summary of what they're paying. They can still un-ready themselves if they realise they forgot something — that flips status back to `joined` and broadcasts `participant.unready`. The room is "closed" automatically when two conditions are both true: every participant with `status IN ('joined','ready')` is in fact `ready`, and the sum of assigned quantities equals the original quantity for every item (no orphan items left unclaimed). On that transition the server emits `split.completed` and the app navigates to the final breakdown screen.

The final breakdown shows the total, every participant's amount with the items behind it expanded, and the option to either confirm "we paid like this" — which persists the result and writes a `check_split_completed` notification to each participant — or to propose the D20 "Choose One to Pay for All" game.

## "Choose One to Pay for All" — unanimous consent

The dice game is gated behind unanimous consent from every registered participant. Proposing it does not roll the dice; it opens a vote.

A participant proposes the game by tapping the button on the split-summary screen. The server creates a `dice_proposals` row with `status='pending'` and `proposed_by` set to that user. For every other registered participant of the check it inserts a `dice_proposal_votes` row with `vote='pending'`. The proposer's own vote is set to `accept` automatically. A partial unique index `dice_proposals(check_id) WHERE status='pending'` ensures only one proposal can exist at a time per check.

Every other participant receives a `dice_proposal_created` notification with two action buttons — "I'm in" and "No thanks" — and an in-room banner that says "Anna proposes the dice. 3 of 5 voted." Their vote goes through `POST /api/dice-proposals/{id}/vote` with body `{"vote": "accept"}` or `{"vote": "decline"}`, which updates their `dice_proposal_votes` row and broadcasts `dice_proposal.voted` on the `check:{id}` channel so every device sees the tally update.

The proposal resolves automatically the moment its fate is decided. If any single vote is `decline`, the server transitions the proposal to `status='declined'`, broadcasts `dice_proposal.resolved` with `outcome='declined'`, and sends each participant a `dice_proposal_resolved` notification — the game is off, the split goes through normally. If every vote is `accept`, the server transitions the proposal to `status='accepted'`, broadcasts `dice.rollStarting`, and rolls the dice server-side. The server is the source of truth for the random numbers, so all phones see exactly the same rolls. Roll-per-participant events `dice.rolled` stream out in sequence with a deliberate delay so each device can animate the D20 dropping; the highest number wins. A `kind_soul_events` row is written with `proposal_id` linking back to the proposal, the proposal flips to `status='completed'`, and the winner receives a `kind_soul_awarded` notification. The "Добра Душа" leaderboard counts this user's `total_paid_for_others` from the new row.

A pending proposal can also be cancelled. If any voter leaves the room before voting (`check_participants.status` transitions to `left`), their vote is treated as `decline` and the proposal is auto-cancelled with `cancel_reason='participant_left'`. If the proposer themselves cancel, the proposal moves to `status='cancelled'`. In both cases the `check:{id}` channel emits `dice_proposal.resolved` so every device updates its UI.

## Raid chat

Every raid gets a dedicated group chat automatically. When a raid is created via `POST /api/raids`, the server inserts a `conversations` row with `type='group'` and `raid_id` set to the new raid, and adds the organizer as the first `conversation_participants` row with `role='admin'`. The conversation's `title` defaults to the raid's title; the conversation's `image_url` defaults to the raid's cover image. Because `conversations.raid_id` is `UNIQUE`, there is exactly one chat per raid.

Chat membership is kept in sync with raid membership by the application layer. On every `raid_participants` row inserted or updated with `status IN ('going','maybe')`, the same user is added to `conversation_participants` for the raid's conversation if they aren't already there. On a row deleted (or status transitioned to `declined`), the participant is soft-removed from the conversation by setting `left_at=now()` so they retain history but stop receiving new messages. Membership changes broadcast `conversation.participant.added` and `conversation.participant.removed` on the conversation channel so other members see the roster update live.

In the mobile app the raid detail screen has a prominent "Open chat" button alongside the RSVP buttons; from inside the chat there's a header chip that links back to the raid detail. This is where members coordinate before the raid ("on my way", "running late by 20"), share photos during, and recap afterwards. Push notifications for new messages in a raid chat carry the raid context, so tapping the notification deep-links straight to that chat screen.

Without this, raid members would have no way to communicate inside the app: friend-list direct messages don't include guests-of-guests, and ad-hoc group chats would require manually replicating the raid's roster. The auto-attached raid chat keeps everything in one place.

There are now four shapes of `conversations` rows the app needs to handle: `type='direct'` (exactly two participants — a 1-on-1 DM), `type='group'` with `friend_group_id` set (chat for a saved friend group / "Party for Dungeon"), `type='group'` with `raid_id` set (a raid chat), and `type='group'` with neither (an ad-hoc group chat created by picking some friends). The same UI renders all four; only the title, image, and the "linked entity" header chip differ.

## Message states: sent, delivered, read

Every outgoing message goes through four states on the sender's side, rendered as a tick icon next to the message:

| State | Icon | Condition |
|---|---|---|
| Pending | grey clock | The user pressed send; HTTP request is in flight. Optimistic — the message is already in the chat list, faded slightly. |
| Sent | single grey check | The server returned 201 with the persisted message id. The clock flips to a check. |
| Delivered | double grey check | Every other participant's device has acknowledged receipt — either over an open WebSocket or via a confirmed push delivery receipt. |
| Read | double accent check | Every other participant's `last_read_at` is at or after the message's `created_at`. |

For 1-on-1 chats the comparison is against the single other participant. For group chats the rules quantify across all other participants — a message is only "Read" once *everyone* read past it. The API returns a `delivered_to_count` and `read_by_count` on each message so the client can also render "Read by 3 of 5" inline if the user taps a message in a group chat, without changing the headline tick state.

The two watermarks that drive everything live on `conversation_participants`: `last_delivered_at` (set when the user's device receives a message) and `last_read_at` (set when the user opens the conversation past that message). Both are monotonically increasing.

The lifecycle plays out like this. The sender's client POSTs to `/api/conversations/{id}/messages`. The server inserts the `messages` row, fires the existing trigger that bumps `conversations.last_message_at`, and replies 201 to the sender — at this point the sender's tick goes to "sent." The server then publishes `message.new` on `conversation:{id}`. Every connected recipient's WebSocket forwards the frame; the recipient's client immediately acknowledges by sending a `delivery.ack` frame back over the same socket. The server bumps that recipient's `last_delivered_at` and broadcasts `delivery.update` to the conversation channel. The sender's client patches its cache, sees the message is now "delivered to N" — if N equals the count of other participants, the tick becomes double-check.

When a recipient opens the conversation screen, the client calls `POST /api/conversations/{id}/read` with the timestamp of the newest visible message. The server clamps `last_read_at = greatest(last_read_at, body.timestamp)` and broadcasts `read.update`. The sender's client patches its cache and the tick flips to the accent colour.

For offline recipients (no open WebSocket), delivery is confirmed differently. The server enqueues an Expo Push notification with the message preview and a `data.messageId` payload. Expo's push receipts endpoint returns success/failure once the device's APNs or FCM has accepted the notification. The push worker treats a successful receipt as a delivery and bumps `last_delivered_at` accordingly, then broadcasts `delivery.update` on the WebSocket so any *other* participants who are online (including the sender on another device) see the tick update without polling.

Edits and deletes are out of scope for the initial chat MVP but the column layout supports them: `messages.edited_at` and `messages.deleted_at` are already in the schema, and `message.edited` / `message.deleted` events on the conversation channel are reserved.

## Tavern Tales — AI Dungeon Master

Tavern Tales is an in-app, AI-powered D&D experience for solo play, designed to fill 5–15 minutes of waiting time at the bar with a real interactive quest. It uses the fantasy race the user already earned from the quiz, lets them pick a class, and lets them play short adventures in one of three modes that vary the AI's tone and rules-strictness. The feature lives in a dedicated fifth tab in the mobile app.

The first time a user opens Tavern Tales they go through a one-screen character creation wizard. Race is fixed — it's whatever `users.race_id` resolved to from the quiz. The user picks a class from the twelve standard 5e options (Barbarian, Bard, Cleric, Druid, Fighter, Monk, Paladin, Ranger, Rogue, Sorcerer, Warlock, Wizard, surfaced from the `dnd_class_info` reference table with descriptions and primary abilities), gives the character a name, and optionally an alignment. The server inserts a `dnd_characters` row, rolls initial ability scores using the standard array (15 / 14 / 13 / 12 / 10 / 8 with class-appropriate placement) into `stats JSONB`, computes starting HP and AC, and returns the character sheet.

After that, a user can start a play session at any time. The session-start screen asks for a mode — described below — and creates a `dnd_sessions` row in `status='active'` (the partial unique index `WHERE status IN ('active','paused')` keeps a character to a single quest at a time, so the user can't accidentally fork their story). The AI then generates an opening scene — a quest hook, the setting, an inciting incident — and the rest is a turn-by-turn chat between the user and the AI dungeon master, persisted as rows in `dnd_messages` keyed by `(session_id, created_at)`.

### Three modes

Munchkin is the quickest, silliest experience. The AI is told to lean into puns, broken builds, ridiculous loot, and 5-minute pacing. It does not enforce D&D rules rigorously; if the player says "I roll to seduce the dragon" the AI just plays along. Responses are 2–4 sentences. This mode is the default for users who tap "I just want something fun."

Normal is the beginner-friendly mode. The AI runs a classic fantasy quest with simple rules, offers 2–3 clear choices each turn, and explains anything the player might not know. Responses are 3–5 sentences. It tracks HP and inventory but doesn't burden the player with bookkeeping. This is the recommended mode for first-time D&D players.

Dungeon Master Pro (Roll20-style) is the strict 5e experience. The AI calls for ability checks with explicit DCs, runs combat with attack rolls, saving throws, damage rolls, AC, and initiative, tracks resources properly, and uses dice notation (`roll a DC 15 Wisdom save`, `2d6 + 3 fire damage`). All rolls are server-side — the FastAPI service produces the random number, persists the result as a `dnd_messages` row with `role='dice_roll'` and the `metadata` JSONB carrying the dice / modifier / DC / purpose, then forwards it to the AI as the next turn's input so the AI's narration matches the actual outcome. The mobile UI renders dice-roll messages distinctly (a die icon, the result big and highlighted, the purpose underneath). This mode is for users who want a real tabletop feel.

### Conversation flow and streaming

A turn in any mode goes like this. The user types into the input box at the bottom of the session screen and hits send. The client POSTs to `POST /api/dnd/sessions/{id}/messages` with the body. The server inserts a `dnd_messages` row with `role='user'`, then opens a streaming call to OpenAI's chat completions API for GPT-4o with three parts assembled into the prompt: a system message that encodes the mode's behaviour (different per mode), a compressed context block built from the session's `summary` plus the character sheet, and the most recent N message rows. As the model streams tokens back, the server forwards each chunk over the user's WebSocket as `dnd.message.partial` events; the mobile screen renders the text growing word by word. When the stream completes, the server inserts the final `role='assistant'` row with the full content, an updated `tokens_in` and `tokens_out`, and any extracted `state_change` payload (HP delta, inventory diff, XP gain) it applied to the character. It bumps `dnd_sessions.turn_count`, `last_message_at`, `input_tokens_used`, `output_tokens_used`, and the user's `dnd_usage_quota.daily_tokens_used` and `monthly_tokens_used` counters. A final `dnd.message.complete` event closes the turn on the client.

When the AI asks for a dice roll in DM Pro mode, its response includes a structured `request_roll` in the `metadata` JSONB (for example `{"dice":"d20","modifier":3,"dc":15,"purpose":"sneak past the guard"}`). The mobile UI renders a "Roll" button below the message; tapping it calls `POST /api/dnd/sessions/{id}/roll` with the request id, the server generates the random number, persists a `role='dice_roll'` row, and feeds it to the next assistant turn automatically. A `dnd.dice_roll` event also fires over the WebSocket so the UI animates the die.

When the rolling summary in `dnd_sessions.summary` is shorter than the cumulative message log by a configurable threshold (default: 20 turns), the server asks the model to extend the summary with the latest exchanges, and trims the oldest messages from the live context window. This keeps long sessions cheap without losing narrative continuity.

### Usage quota and cost control

LLM cost is the one variable that matters for a real deployment. `dnd_usage_quota` holds a daily and monthly token cap per user (defaults: 30k / day, 500k / month — roughly 5–10 sessions per day, 100 per month). Every turn checks the cap before calling OpenAI; if exceeded, the API responds `429 Too Many Requests` with a structured payload describing the user's quota and reset time, and the mobile screen shows a friendly "you've used your quests for today" message. A nightly cron resets daily counters; a monthly cron resets monthly. Admins can raise individual caps via direct row update if needed.

### Endpoints and events

REST endpoints under `/api/dnd`: `GET /api/dnd/classes` (returns `dnd_class_info` for the picker), `GET /api/dnd/characters`, `POST /api/dnd/characters`, `GET /api/dnd/characters/{id}`, `PUT /api/dnd/characters/{id}` (manual level-up or sheet edit; AI also writes here through internal API), `DELETE /api/dnd/characters/{id}` (soft delete), `GET /api/dnd/sessions` (filter by status), `POST /api/dnd/sessions` (body: `character_id`, `mode`), `GET /api/dnd/sessions/{id}` (full session including messages), `POST /api/dnd/sessions/{id}/messages` (the streaming turn — see above), `POST /api/dnd/sessions/{id}/roll` (resolve an AI-requested dice roll), `POST /api/dnd/sessions/{id}/pause`, `POST /api/dnd/sessions/{id}/resume`, `POST /api/dnd/sessions/{id}/end`, `GET /api/dnd/usage` (current quota counters and limits).

WebSocket events on the `user:{userId}` channel, all carrying a `session_id` in the payload: `dnd.message.partial` (streaming token chunk), `dnd.message.complete` (final assistant message with metadata), `dnd.dice_roll` (resolved roll), `dnd.state_change` (character/session state diff applied), `dnd.session.ended`.

### Mobile screens

The fifth tab "Tavern Tales" opens to one of two screens depending on state: if the user has no character, it shows the character-creation wizard; if they do, it shows a quest selector. The quest selector is a small home that shows the current character at the top (avatar, race, class, level, current HP), a "Continue quest" card if a session is active or paused, and below it a mode picker that starts a brand-new quest with one tap. The active-session screen is a chat layout — assistant text in the centre, user input at the bottom, a small character HUD pinned to the top with HP and the current location pulled from `dnd_sessions.metadata`. Dice-roll messages get a distinct die-icon styling so they're easy to scan. A drawer from the right reveals the full character sheet, inventory, and quest log.

### Tie-ins with the rest of the app

Tavern Tales is intentionally self-contained but a few touchpoints land naturally. The race the user got from the quiz drives the AI's flavour prompts and (in DM Pro mode) the character's traits. New achievements key off Tavern Tales activity: `first_quest_completed`, `reached_level_5`, `tried_all_three_modes`, `kind_dm` (completed a quest without losing HP), `chaos_munchkin` (completed five Munchkin runs). A push notification of type `dnd_session_reminder` re-engages users who paused a quest more than a day ago. Friends can see in each other's profile pages how many quests they've completed and which class they're playing — without exposing the actual story content.

## Database schema (summary)

The full DDL is in `database/schema.sql`; the design rationale is in `database/SCHEMA.md`. Here is the table inventory grouped by purpose.

Reference and lookup data: `cities` (with `GEOGRAPHY` location), `vibes`, `drinks`, `races`, and the affinity join tables `race_drinks` and `race_vibes`. Users and auth: `users`, `refresh_tokens` (storing only SHA-256 hashes of the refresh value), `push_tokens` (Expo / APNs / FCM device tokens). Bars: `bars` (with `tsvector` search column, denormalized `rating_avg`/`rating_count`, and a `JSONB work_hours`), `bar_vibes`, `bar_photos`, `bar_reviews` (one per user per bar), `bar_favorites` (composite PK). Quiz: `quiz_questions`, `quiz_answers`, `quiz_answer_races` (with `score`), `user_quiz_results`. Social: `user_friends` (symmetric, two rows per accepted friendship), `friend_requests` (with a partial unique index on pending pairs), `friend_groups`, `friend_group_members`. Raids: `raids` (with optional override `GEOGRAPHY` location), `raid_participants`. Checks and the split room: `checks`, `check_items`, `check_participants` (with lifecycle `status`: invited → joined → ready → left), `check_item_assignments`, `dice_proposals` (one pending per check, partial unique index), `dice_proposal_votes` (one row per registered voter), `kind_soul_events` (one per check, linked back to its `dice_proposals` row). Gamification: `achievements`, `user_achievements`. Notifications: `notifications` (extended `type` enum now includes `check_invite`, `check_split_completed`, `dice_proposal_created`, `dice_proposal_resolved`, `dnd_session_reminder`). Chat: `conversations` (optionally linked 1:1 with a `friend_group` or with a `raid`), `conversation_participants` (with `last_delivered_at` and `last_read_at` watermarks driving the message-state ticks), `messages` (with `jsonb_array_length` check that body or attachments is non-empty), `message_reactions`, `user_presence`. Tavern Tales: `dnd_class_info` (reference), `dnd_characters` (linked to `users` and `races`, with HP/AC/stats and JSONB inventory and spells), `dnd_sessions` (one active or paused per character, partial unique index), `dnd_messages` (turn log with user / assistant / dice_roll / narration roles), `dnd_usage_quota` (per-user LLM token caps).

Totals: 44 tables, 23 enum types, 54 indexes, 12 triggers, 68 foreign keys — all validated through `pgsql-parser`.

## REST API surface (planned)

Auth lives under `/api/auth`: `POST /register`, `POST /login`, `POST /refresh`, `POST /logout`, `GET /me`. User profile is `/api/users/me` (GET, PUT) and `/api/users/{id}` (GET public profile). Cities, races, drinks, and vibes have read-only `GET` collection endpoints. Bars sit under `/api/bars` with list (filter and full-text), detail, and admin-only create/update. Reviews are nested: `/api/bars/{id}/reviews` (GET, POST), `DELETE /api/reviews/{id}`. Favorites: `POST /api/bars/{id}/favorite`, `DELETE /api/bars/{id}/favorite`, `GET /api/users/me/favorites`.

Quiz is `GET /api/quiz` (returns questions + answers; the server does not reveal per-answer race scores), `POST /api/quiz/submit` (returns the assigned race). Friends and social: `GET /api/users/me/friends`, `GET /api/friend-requests` (incoming + outgoing), `POST /api/friend-requests` (send), `POST /api/friend-requests/{id}/accept`, `POST /api/friend-requests/{id}/decline`. Friend groups: `/api/friend-groups` CRUD plus `/api/friend-groups/{id}/members` for adding and removing. Raids: `/api/raids` CRUD, with a near-me query `GET /api/raids?near=lat,lon&radius=km`, and `POST /api/raids/{id}/rsvp` for status changes.

Checks and the split room: `POST /api/checks` (creates header + uploads image URL), `POST /api/checks/{id}/parse` (kicks off OCR; runs as a background task with status pollable on the check), `POST /api/checks/{id}/participants` (invite registered users or add guests — sends `check_invite` notifications), `POST /api/checks/{id}/participants/me/join` (accept invitation, transition `status` to `joined`), `POST /api/checks/{id}/participants/me/ready` and `/unready` (toggle `ready` status), `POST /api/checks/{id}/participants/me/leave` (set `status='left'`), `PUT /api/checks/{id}/items/{itemId}/assignments` (claim or release a quantity of an item — caller can only edit their own assignments), `GET /api/checks/{id}` (the full check with items, participants, assignments, and computed totals). Dice: `POST /api/checks/{id}/dice-proposals` (open a proposal; returns 409 if one already pending), `POST /api/dice-proposals/{id}/vote` with body `{vote: 'accept' | 'decline'}`, `POST /api/dice-proposals/{id}/cancel` (proposer only). Notifications: `GET /api/notifications`, `POST /api/notifications/{id}/read`, `POST /api/notifications/read-all`. Chat: `GET /api/conversations` (inbox), `POST /api/conversations` (create direct or ad-hoc group), `GET /api/conversations/{id}/messages` (paginated, cursor-based), `POST /api/conversations/{id}/messages`, `POST /api/conversations/{id}/read` (updates `last_read_at`), `POST /api/conversations/{id}/delivery` (HTTP fallback for `last_delivered_at`; normally bumped via the WebSocket `delivery.ack` frame), `POST /api/messages/{id}/reactions`.

Push token registration: `POST /api/push-tokens`, `DELETE /api/push-tokens/{token}`. Achievements: `GET /api/achievements`, `GET /api/users/me/achievements`. All write endpoints require a valid access token; admin endpoints additionally require `role = admin`.

## Real-time / WebSocket protocol

A single WebSocket endpoint at `/ws` is the only socket the app keeps open. Authentication happens via a one-time ticket: the client calls `POST /api/auth/ws-ticket`, receives a short-lived (60 second) token, and connects to `wss://server/ws?ticket={token}`. The server validates the ticket, loads the user, registers the connection in its in-memory map keyed by user id, and subscribes the connection to the relevant Redis Pub/Sub channels.

Channels are: `user:{userId}` (private, for events targeted at this user — friend requests, achievement unlocks, raid invites, presence updates of friends), `conversation:{conversationId}` (for chat messages, delivery and read receipts, reactions, and typing indicators in a conversation the user is a participant of), and `check:{checkId}` (for the split-room flow — participants joining, item assignments updating, totals re-computing, dice proposals voting, dice rolling). The client maintains a small dispatcher that routes each event type to an RTK Query cache patch — `message.new` appends to the messages query for that conversation; `friend.accepted` invalidates the friends query; `assignment.updated` patches the relevant check; and so on.

Conversation channel events: `message.new` (new persisted message), `message.edited`, `message.deleted`, `delivery.update` (a participant's `last_delivered_at` advanced — sender's tick goes to double-check when this covers everyone), `read.update` (a participant's `last_read_at` advanced — sender's tick flips to accent colour when this covers everyone), `reaction.added`, `reaction.removed`, `typing.start`, `typing.stop`, `conversation.participant.added` (used by raid chats when a user RSVPs), `conversation.participant.removed`.

Check channel events for the split room: `participant.joined`, `participant.ready`, `participant.unready`, `participant.left`, `assignment.updated` (an item assignment changed — body carries the patched row), `totals.updated` (carries the recomputed `per_participant: {participant_id: amount}` map), `split.completed` (every joined participant is ready and every item is fully assigned). Dice proposal events on the same channel: `dice_proposal.created`, `dice_proposal.voted` (carries the per-user tally), `dice_proposal.resolved` (`outcome: 'accepted' | 'declined' | 'cancelled'`), `dice.rollStarting`, `dice.rolled` (per-participant, with the resolved D20 number), `kind_soul.awarded` (with the winning user).

Client-to-server messages on the same socket: `presence.heartbeat` every 25 seconds (so the server knows the device is still alive and updates `user_presence`), `typing.start` and `typing.stop` (not persisted; the server simply re-broadcasts to the conversation channel), `read.mark` when the user scrolls a conversation (the server updates `last_read_at` and emits `read.update`), and `delivery.ack` immediately after the client renders a `message.new` (the server updates `last_delivered_at` and emits `delivery.update`).

Disconnection is detected when the server's WebSocket loop raises; the connection is removed from the in-memory map, the user's `user_presence.status` is set to `offline` if no other connection for that user remains, and a `presence.update` is broadcast to that user's friends. The client side reconnects with exponential backoff on `onclose`, fetching a fresh ticket each time.

## Mobile app structure

The Expo Router layout uses tabs at the root with stack navigation inside each tab. The folder structure under `app/` mirrors the routes: `app/(auth)/login.tsx` and `app/(auth)/register.tsx` for the unauthenticated stack, with a layout that redirects already-authenticated users to the main tabs; `app/(tabs)/_layout.tsx` defines the four-tab navigator; `app/(tabs)/index.tsx` is the Home feed; `app/(tabs)/bars/index.tsx` is the catalog and `app/(tabs)/bars/[id].tsx` is the detail page; `app/(tabs)/friends/index.tsx` is the friends list with chat inbox, with sub-screens for individual conversations under `app/(tabs)/friends/chat/[conversationId].tsx`; `app/(tabs)/profile/index.tsx` is the profile with edit and history under sub-routes. Modal flows (receipt scan, D20 dice, quiz) are pushed as modals from the relevant tab.

State is organised in two layers. Server data goes through RTK Query — one API "slice" per resource group (`barsApi`, `chatApi`, `friendsApi`, `raidsApi`, `checksApi`, `quizApi`, `achievementsApi`). Local state — current theme, draft chat input, pending uploads, WebSocket connection status — lives in a small set of Redux Toolkit slices. A `socketMiddleware` listens for events arriving on the WebSocket and dispatches the corresponding RTK Query cache updates so that screens re-render automatically. Secure storage holds the refresh token; the in-memory access token is rotated transparently by an `axios` (or `fetch`) interceptor.

The Tamagui theme defines two colour palettes — a warm "tavern" dark theme as the default, and a lighter alternative — plus typography ramps and the accent colour from the original project's design (a saturated teal for active elements). All screens use Tamagui components (`YStack`, `XStack`, `Button`, `Card`, `Sheet`, etc.) so the visual language stays consistent without manual styling per screen.

## Demo plan (two phones)

For the demonstration the backend runs either on your laptop (with both phones connected to the same Wi-Fi network and the laptop's local IP baked into the app's `API_BASE_URL`) or on a free-tier deployment such as Fly.io or Railway. The laptop option is simpler and works without internet, which makes it the safer default. Concretely: start PostgreSQL and Redis with `docker-compose up`, start the FastAPI server with `uvicorn app.main:app --host 0.0.0.0 --port 8000`, find the laptop's LAN IP, and set `EXPO_PUBLIC_API_BASE_URL=http://192.168.x.x:8000` for both phones. Both phones install the Expo Go app and scan the QR code from `npx expo start`. Each phone registers a separate account, sends a friend request to the other, accepts it on the second device, then opens a chat. The first phone sends a message; the second phone sees it appear instantly. A receipt photo from one phone, OCR'd, can be split with the second user as a participant, and the dice roll outcome shows simultaneously on both devices because the result is broadcast over the same WebSocket channel.

For going beyond the local demo (so the examiners can use the app from their own phones at any time), the easiest path is Fly.io for the FastAPI + Redis containers and Neon or Supabase for the managed Postgres with PostGIS. The mobile app is built with `eas build --profile preview` to produce installable `.apk` / `.ipa` artefacts.

## Security posture

Passwords are stored as Argon2 hashes via `passlib`. Access tokens are HS256-signed JWTs with a 15-minute TTL; refresh tokens are 64-byte random strings whose SHA-256 hash is stored in `refresh_tokens` (the raw value is only ever in the client's secure storage). Refresh-on-use rotates the refresh token — the old hash is revoked, a new one is issued — so a leaked refresh token has a small window of usefulness. The WebSocket ticket flow ensures we never put the JWT in a query string (which can be logged by proxies) and gives the server a chance to revoke a single connection without invalidating the user's session. All input is validated by Pydantic models on the FastAPI side; SQL is parameterised via SQLAlchemy. Foreign keys with explicit `ON DELETE` actions prevent orphaned rows. Soft-deleted users (`users.deleted_at IS NOT NULL`) are filtered out of queries via a session-level filter. Image uploads go through presigned S3 URLs scoped to a single object key, so the API server never proxies bytes. Rate limiting will be added at the edge (Nginx or a Cloudflare WAF rule) for the auth endpoints.

## Project structure

The repository is a monorepo with two top-level packages and the database assets at the root.

```
DiplomaProject/
├── PROJECT.md                 ← this file
├── database/
│   ├── schema.sql             ← full DDL (PostgreSQL)
│   └── SCHEMA.md              ← schema design rationale
├── backend/                   ← FastAPI app (to be scaffolded)
│   ├── pyproject.toml
│   ├── alembic/
│   └── app/
│       ├── main.py
│       ├── core/              ← config, security, deps
│       ├── db/                ← SQLAlchemy session + models
│       ├── auth/              ← register/login/refresh/ws-ticket
│       ├── bars/              ← routers, services, schemas
│       ├── checks/
│       ├── chat/
│       ├── friends/
│       ├── raids/
│       ├── quiz/
│       ├── achievements/
│       ├── notifications/
│       ├── realtime/          ← WS endpoint, connection manager, Redis pub/sub
│       └── tasks/             ← background workers (OCR, achievement evaluator)
└── mobile/                    ← Expo app (to be scaffolded)
    ├── package.json
    ├── app.config.ts
    ├── tamagui.config.ts
    ├── app/                   ← Expo Router routes (see "Mobile app structure")
    ├── src/
    │   ├── store/             ← Redux store + slices
    │   ├── api/               ← RTK Query API definitions
    │   ├── realtime/          ← WebSocket client + middleware
    │   ├── components/        ← shared Tamagui components
    │   ├── features/          ← feature-grouped UI (bars, chat, checks, raids…)
    │   └── theme/             ← Tamagui theme tokens
    └── assets/
```

## Roadmap

The work is split into phases that each end with something demoable.

Phase 1 — Foundation. Get PostgreSQL + Redis running locally via `docker-compose`. Apply the schema via Alembic migrations. Scaffold the FastAPI app, the auth endpoints (register, login, refresh, ws-ticket, me), and the WebSocket endpoint with a stub handler. Scaffold the Expo app with Tamagui, Expo Router, Redux Toolkit, and a login screen that talks to the backend. End state: a user can register and log in from a phone.

Phase 2 — Bars. Implement the bar catalog endpoints, full-text search, reviews, favorites, and photos. Build the catalog screen, detail screen, favorites screen. Seed Lviv bars. End state: browse and favorite bars on the phone.

Phase 3 — Social. Friends, friend requests, friend groups. Notifications table + screen. Push token registration via Expo Push. End state: two accounts can become friends and see each other's basic activity.

Phase 4 — Chat. Conversations, messages, reactions. WebSocket message flow with Redis Pub/Sub fan-out. Mobile chat UI with optimistic sending, read receipts, typing indicators, offline push fallback. End state: two phones can chat in real time — this is the multi-device demo requirement.

Phase 5 — Raids. Raid creation, RSVP, near-me geo queries, push reminders. End state: organise a meet-up at a bar with friends.

Phase 6 — Receipts and D20. Image upload, OCR via OpenAI Vision, item parsing, participant assignment, totals, D20 dice screen, `kind_soul_events`, leaderboard. End state: split a real receipt with a friend on the second phone.

Phase 7 — Quiz and achievements. Quiz delivery and scoring, race assignment, achievement evaluator running off domain events, achievement screen, race-themed profile decoration. End state: gamification loop closed.

Phase 8 — Tavern Tales (AI DM). Character creation, the three-mode system prompt suite, GPT-4o streaming through the WebSocket, server-side dice rolling, rolling session summary, quota enforcement, the fifth tab UI, and the D&D-specific achievements. End state: a user can finish a 10-minute solo quest from start to finish on the phone.

Phase 9 — Polish and deploy. Animations, empty states, error boundaries, accessibility pass, EAS preview builds, server deploy. End state: shareable demo build.

## Open questions

A few decisions are deferred until we hit them in code. Should the OCR call be synchronous (slow request, simple client) or asynchronous with a job + SSE updates (better UX, more moving parts)? Likely async, but we'll start sync and refactor. Do we need typing indicators in MVP? Probably not for Phase 4 — they're a Phase 9 polish item. Do reactions go in MVP? Yes, they're cheap. Will we host images on Cloudflare R2 or AWS S3? Either; R2 is cheaper but S3 has more mature SDKs — defer until deploy time. Should the FastAPI WebSocket layer migrate to `python-socketio` if rooms become awkward? We'll re-evaluate when the per-conversation channel count grows past a few thousand. For Tavern Tales: what's the right default LLM token cap per user, and do we want a paid tier later? Defaulting to 30k/day and 500k/month gives ~100 quests a month; we'll observe and tune.

## References

The original coursework documentation (`Інтернет-проєкт КР.docx`) is the source of the functional requirements and the database entity list that this rebuild is faithful to. The full DDL is in `database/schema.sql`; the schema rationale is in `database/SCHEMA.md`.
