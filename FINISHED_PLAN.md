# Tavern Tales — Finishing Plan & Gap Analysis

**Date:** 2026-06-08
**Purpose:** Reconcile the product vision (Section 6 of *Main Plan.md*) with the current codebase, then lay out exactly what's left to build to ship the app as described.

**Decisions locked in for this plan:**
- **Parties** are a *separate new feature* from Raids (own model, API, screens).
- **Navigation** is *reworked* to the Section 6 footer: Search · Social · Create · Messages · AI D&D.
- **Social rating** is a *full system* (points, no-show penalties, attendance/ditch statistics).

---

## Part A — Vision vs. Reality (gap matrix)

Legend: ✅ done · 🟡 partial · ❌ missing

| Vision (Section 6) | Status | Where it lives today | Gap to close |
|---|---|---|---|
| Login / signup | ✅ | `backend/app/auth/*`, `mobile/app/(auth)/*` | — |
| Onboarding quiz → assigns race | ✅ | `backend/app/quiz/*`, `mobile/app/quiz/index.tsx` | Confirm quiz is forced once after first signup |
| Home: popular bars | 🟡 | `mobile/app/(tabs)/index.tsx`, `bars` API | Add "popular" ranking endpoint/sort |
| Home: bars visited by friends + **friends-only ratings** | ❌ | — | New endpoint: friend-scoped visit feed with friend-only rating aggregate |
| Home: raids near you | 🟡 | `raids` list (has geo column) | Add radius/"near me" query by user location |
| Home: people searching for party members | ❌ | — | Depends on new Parties feature |
| Header: logo + avatar → profile | 🟡 | home screen header | Wire avatar tap to profile; logo slot reserved (user supplies asset) |
| **Raids** core (theme, location, time, max people) | 🟡 | `backend/app/raids/*` | `title/description` exist; add explicit *theme*, rename/extend fields |
| Raid visibility: open-to-all vs friends-only | ❌ | — | Add `visibility` enum + filtering |
| Join raid (RSVP) | ✅ | `raids/rsvp` | — |
| **Can't be in two raids at the same time** | ❌ | — | Conflict check on overlapping `scheduled_at`..`ends_at` |
| **Checkpoint-reached** button (user marks arrival) | ❌ | — | New RSVP→`arrived` transition + endpoint |
| **Host verifies attendance** | ❌ | — | Host-only endpoint to confirm/deny each participant |
| Host **abort / finish early** | 🟡 | `raids/cancel` exists | Add `complete`/`abort_early` states distinct from cancel |
| **Parties** (find party members) | ❌ | — | Whole new module |
| Party requires **bio + interest chips** | ❌ | `users` has no bio/interests | New `interests` catalog + user bio/interests |
| Party matching by interests | ❌ | — | Matching query |
| Party full → "party is already full" | ❌ | — | Capacity check + error |
| Footer: 5 positions (Search/Social/Create/Messages/AI&D&D) | ❌ | tabs = Home/Map/Bars/Friends/Profile | Restructure `(tabs)/_layout.tsx` |
| Social cards w/ 3 attendance signals (friends going / friends-only / nobody you know) | ❌ | — | Card component + per-viewer relationship computation |
| Messages | ✅ | `backend/app/chat/*`, `mobile/app/chat/*` | — |
| AI D&D game | ✅ | `backend/app/tavern_tales/*`, `mobile/app/tavern/*` | — |
| **Post-event check**: host photographs bill, AI parses, payroll to attendees | 🟡 | `backend/app/checks/*` (OCR + split + dice) | Checks are standalone — link to a raid/party; auto-create on event end |
| Attendees notified → pick their items + quantity | 🟡 | `check_items`, `check_item_assignments` | Add quantity-per-user; notification trigger from event end |
| **Social rating** (no-show penalty) | ❌ | — | Rating field + penalty engine |
| User **statistics** (attended / ditched / etc.) | ❌ | — | Stats aggregation + profile UI |

**Summary:** the engine-room pieces (auth, quiz, bars, chat, AI D&D, OCR bill-split with dice) are built. The *social-event lifecycle* — Parties, raid attendance verification, event→check linkage, interests/matching, and the rating/stats layer — is the bulk of remaining work, plus a navigation rebuild.

---

## Part B — Work packages (the finishing plan)

Ordered by dependency. Each package lists backend + mobile work and a "done when" check.

### WP1 — User profile foundation (bio, interests, rating, stats)
Everything social depends on this, so it goes first.

**Backend**
- Migration: add to `users` → `bio TEXT`, `social_rating INT DEFAULT 100` (or chosen baseline), `events_attended INT`, `events_ditched INT`.
- New tables: `interests` (catalog: hiking, tabletop, dnd, …) and `user_interests` (M2M).
- New module `app/profile/` or extend `app/users/`: endpoints to read/update bio, set interests (chips), read rating + stats.
- Reference endpoint to list all interest chips (extend `app/reference/`).

**Mobile**
- Extend `profile/edit.tsx`: bio field + interest-chip selector.
- Profile screen: show rating, attended/ditched stats.
- New `interestsApi` / extend `referenceApi` and `usersApi`.

**Done when:** a user can set a bio + interests and see their rating and attendance stats.

---

### WP2 — Raid lifecycle completion
Bring raids up to the Section 6 spec.

**Backend** (`app/raids/`)
- Schema/model: add `theme` (or repurpose), `visibility` enum (`open` / `friends_only`).
- RSVP states: extend enum to `going` → `arrived` (checkpoint) → `attended`/`no_show` (host-verified).
- New endpoints:
  - `POST /raids/{id}/checkpoint` — participant marks "I'm here".
  - `POST /raids/{id}/participants/{uid}/verify` — host confirms attendance (`attended` / `no_show`).
  - `POST /raids/{id}/complete` and `POST /raids/{id}/abort` — host ends event (distinct from `cancel`).
- **Two-raid conflict guard** in RSVP service: reject join if user already RSVP'd to another raid overlapping in time.
- Visibility filtering in `list_raids` (friends-only raids only visible to organizer's friends).
- "Near me" filtering by user location radius.
- **Drink-preference soft ranking** (see WP3b): tag raids with drink types and sort the list higher when they overlap the viewer's race-derived drink preferences.

**Mobile** (`app/raids/*`, `raidsApi`)
- Create-raid form: theme, visibility toggle, time, max participants, location picker.
- Raid detail: Join, **Checkpoint reached** button, host's attendance-verification list, host Complete/Abort controls.
- Surface conflict error ("you're already attending another raid at this time").

**Done when:** host creates a raid, users join + check in, host verifies attendance and completes/aborts; double-booking is blocked.

---

### WP3 — Parties (new feature)
Separate from raids: lightweight "looking for party members" with interest matching.

**Backend** — new module `app/parties/`
- Tables: `parties` (host, title, description, interests/tags, max_members, visibility open/friends-only, status), `party_members` (status: invited/joined/left).
- Endpoints: create, list (with interest-based matching + visibility), get, join (**capacity check → "party is already full"**), leave, invite (notify users/friends).
- Gate: user must have bio + ≥1 interest to create/join (ties to WP1).

**Mobile** — `app/party/*` (new), `partiesApi`
- Create-party flow (requires bio/interests; prompt to fill if missing).
- Party list/detail with join + "full" message.
- Invite friends / send notifications.

**Done when:** a user with a bio + interests can create a party, others can discover by interest and join until full.

---

### WP3b — Drink-preference soft ranking (parties + raids)
**Clarified requirement.** A user's alcohol preferences are *not* stored separately — they are **derived from the race assigned by the onboarding quiz**: `user.race_id → race_drinks → drinks`. The quiz already captures this, so no new survey step or `user_drinks` table is needed.

What's missing is *using* those preferences. Effect = **soft ranking** (nothing hidden, matches just float higher).

**Backend**
- Give raids and parties a set of associated **drink types** (reuse the `drink_type` enum: beer/cocktail/wine/spirit/non_alcoholic/other) — e.g. `raid_drinks` / `party_drinks`, or a simple `drink_types[]` column.
- In `list_raids` / `list_parties`, compute an overlap score between the event's drink types and the viewer's race-derived drink types, and use it as a secondary sort key (after distance/recency).

**Mobile**
- Create-raid / create-party: optional drink-type chips for the event.
- Lists already benefit automatically (server-sorted); optionally show a "matches your taste" hint on cards that overlap.

**Done when:** two otherwise-equal events are ordered so the one matching the viewer's race drinks appears first, with nothing filtered out.

---

### WP4 — Navigation rework
Restructure the tab bar to Section 6's footer.

**Mobile** (`app/(tabs)/_layout.tsx` + screens)
- Five tabs: **Search** (bars/fast-food), **Social** (raids + parties as cards), **Create** (raid/party chooser), **Messages**, **AI D&D**.
- Move current Home content (popular bars, friends' visits, raids near you, parties) into Search/Social as appropriate; relocate Profile to header avatar; fold Map into Search or a sub-view.
- **Social cards** with 3 attendance signals computed per viewer: "friends are attending" / "only friends" / "nobody you know is attending."

**Done when:** the footer matches the spec and every feature is reachable.

---

### WP5 — Event → Check linkage (post-event shared bill)
Connect the existing bill-split engine to events. **Applies to both raids and parties** — the trigger is "this gathering had one shared bill," not the event type. If there's no shared bill, the step is simply skipped.

**Core flow (confirmed):** group gathers → host photographs the single shared bill → AI parses line items → each attendee is sent the parsed bill, chooses the positions they ordered + quantity → app computes how much each person owes.

**Backend** (`app/checks/` + raids/parties)
- Add nullable `raid_id` AND `party_id` to `checks` (a check belongs to whichever event produced it; both optional so standalone checks still work).
- On host "complete" of a raid/party that has a bill: host uploads receipt → existing OCR pipeline → check auto-created with all verified attendees as participants.
- Add **quantity per assignment** to `check_item_assignments` (user picks item + qty); ensure per-user owed-amount is computed and returned.
- Notification to each attendee: "select what you ordered."

**Mobile**
- Hook event-completion (raid OR party) into the existing checks/new + dice flow.
- Item-picker with quantity for attendees; show each person's computed total.

**Done when:** finishing a raid or party that had a shared bill launches the photographed-bill split among its attendees, each choosing items + quantities and seeing what they owe.

---

### WP6 — Social rating & statistics engine
Depends on WP2/WP3 attendance data.

**Backend**
- Rating rules: no-show (RSVP'd but not verified attended) → deduct points; successful attendance → maintain/gain.
- Trigger on raid `complete`/verify and party lifecycle; write to `users.social_rating`, increment `events_attended` / `events_ditched`.
- Stats endpoint for the profile.

**Mobile**
- Profile statistics view (attended, ditched, rating, trend).

**Done when:** a no-show measurably drops a user's rating and their stats update.

---

### WP7 — Test coverage & demo build
- Backend tests for the new modules (raids lifecycle, parties, rating, event→check).
- Extend existing pytest suite (currently auth/bars/chat/health/reference only).
- Runtime-verify mobile on a device/emulator; reconcile every RTK Query endpoint with a live route.
- EAS build → installable `.apk`/`.ipa` for the diploma demo.
- Live OpenAI keys for OCR + GPT-4o smoke test.

**Done when:** green tests, a running app on a phone, and an installable artifact.

---

## Part C — Suggested order & rationale
1. **WP1** (profile foundation) — unblocks parties + rating.
2. **WP2** (raid lifecycle) — completes the existing half-built feature.
3. **WP3** (parties) — the biggest missing feature.
4. **WP4** (navigation) — once parties exist there's something to put in the footer.
5. **WP5** (event→check) — ties events to the finished bill-split engine.
6. **WP6** (rating/stats) — needs attendance data from WP2/WP3.
7. **WP7** (tests + demo build) — last.

---

## Part D — Open questions to resolve before/while building
1. **Race vs. role:** is the quiz-assigned "race" used anywhere beyond flavor (e.g., affects matching or stats)?
2. **Rating math:** starting value, points lost per no-show, any decay/recovery, floor/ceiling?
3. ~~**Parties vs Raids overlap:** can a party also have a venue + bill?~~ **RESOLVED:** the shared-bill flow applies to both raids and parties — any gathering with one shared bill gets parsed and split. No shared bill → step skipped.
4. **Friends-only ratings on bars:** is the "rating by friends only" a separate aggregate from a global bar rating, or the only rating shown?
5. **Map:** keep a dedicated map view (fold into Search) or drop the standalone map tab?
6. **Fast-food vs bar:** is "fast food establishment" a `bar` with a type flag, or a separate venue category?
