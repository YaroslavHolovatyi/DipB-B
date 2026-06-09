## Brief

You are a senior product designer specialising in mobile UI/UX for consumer social apps. I need a complete, production-ready design system for a React Native mobile app called **Beer & Beverages** (internal codename: B&B).

### What the app is

Beer & Beverages is a **social bar-finder app with a fantasy tavern skin** — think Untappd meets Dungeons & Dragons. Users find bars ("taverns") near them, plan group visits ("raids"), bring friends along in a "Party", chat in real time, and split the bill from a photo of the receipt. A D20 dice roll decides who pays for everyone, earning the loser the title of "Добра Душа" (Kind Soul). Users take a quiz that assigns them a fantasy race (human, elf, dwarf, etc.), unlock achievements, and climb a leaderboard.

Key screens: **Home feed**, **Bar catalog & Bar detail**, **Raid planner**, **Chat / group chat**, **Split room** (collaborative receipt splitting), **Profile** (race, achievements, stats), **Quiz**, **Notifications**.

---

## Your output

Produce a complete design system document with the four sections below. For every color, provide both a **hex code** and a **Tamagui-compatible token name** (e.g. `$amber9`, `$bgBase`). The app is built with **React Native + Expo + Tamagui**, so all tokens and component specs must be directly usable inside a Tamagui theme object.

---

## Section 1 — Color Palette & Design Tokens

### Mood requirements
- **Vibrant and playful** — energetic enough to compete with apps like Untappd, Foursquare, or Duolingo
- **Fantasy tavern undertone** — warm ambers and golds should appear as accent/highlight colors, evoking candlelight and wooden tavern interiors, without making the whole palette feel dark or muddy
- The primary interactive color should feel **bold and modern**, not retro or sepia-toned
- Support both **light mode** and **dark mode** (dark mode should feel like stepping inside a cozy evening tavern)

### Required token groups

**Background surfaces** (light + dark variants for each):
- `$bgBase` — main app background
- `$bgCard` — card / sheet surface
- `$bgElevated` — modal, bottom sheet, elevated panel
- `$bgInput` — text input field background

**Brand / primary**:
- `$brandPrimary` — main CTA, active tab, primary button fill
- `$brandPrimaryHover` — pressed state
- `$brandPrimarySubtle` — tinted background for chips or selected states

**Fantasy accent (amber/gold)**:
- `$accentGold` — achievement badges, dice roll result, "Kind Soul" crown, raid timers
- `$accentGoldSubtle` — background glow behind gold elements
- `$accentGoldText` — gold text on dark surfaces (must pass AA contrast)

**Secondary accent** (pick one — should complement the primary without clashing):
- `$accentSecondary` — used for "raid" RSVP pill, "party" badge, active raid indicator
- `$accentSecondarySubtle`

**Semantic**:
- `$success` — RSVP "Going", assignment confirmed, split completed
- `$successSubtle`
- `$warning` — "Maybe" RSVP, item unclaimed in split room, session expiring
- `$warningSubtle`
- `$error` — validation errors, "Declined" RSVP, destructive actions
- `$errorSubtle`

**Text**:
- `$textPrimary` — headings, primary labels
- `$textSecondary` — subtext, timestamps, captions
- `$textDisabled`
- `$textOnBrand` — text/icons that sit on top of `$brandPrimary` fill
- `$textOnAccentGold` — text on gold fills

**Borders & dividers**:
- `$borderDefault`
- `$borderStrong`
- `$borderFocus` — input ring on focus

**Special / gamification**:
- Race color for each of the 6 fantasy races (human, elf, dwarf, orc, halfling, gnome) — one pastel fill + one dark text variant per race, so they work as avatar ring / badge backgrounds. Name them `$raceHumanBg`, `$raceHumanText`, etc.
- Leaderboard tier: Gold (`$tierGold`), Silver (`$tierSilver`), Bronze (`$tierBronze`)

For each token provide: hex value, Tamagui token name, light mode value, dark mode value (if different), and one sentence describing when to use it.

---

## Section 2 — Typography System

The app renders on iOS and Android via Expo. Use a **Google Font pairing** that is available in `@expo-google-fonts`. The font system must feel playful and legible on small screens.

### Requirements
- One **display / heading font** — should have personality and a slight fantasy/adventure feel without being unreadable; think bold, confident, slightly rounded or characterful
- One **body / UI font** — clean, highly legible at small sizes, works for chat bubbles, lists, form labels
- Optionally one **monospace / numeral font** for prices, dice rolls, check amounts, timers (can be the same as body if a tabular-nums variant exists)

### Token table

For each font style provide: Tamagui token name, font family, weight, size (sp), line height, letter spacing, and usage notes.

Required styles:
- `$displayXL` — hero number or splash text (e.g. D20 roll result: "17")
- `$displayL` — screen title on landing/onboarding screens
- `$headingXL` — bar name on detail page, raid title
- `$headingL` — section headers (e.g. "Upcoming Raids")
- `$headingM` — card titles, user name on profile
- `$headingS` — subheadings, group chat name
- `$bodyL` — chat message body
- `$bodyM` — list item primary text, review body
- `$bodyS` — secondary label, caption, timestamp
- `$labelL` — button label (bold)
- `$labelM` — tab label, chip text
- `$labelS` — badge text, tag
- `$numericL` — receipt total, split amount, leaderboard score (tabular)
- `$numericM` — item price in split room
- `$numericS` — check subtotal, distance chip

---

## Section 3 — Key Screen Mockups

Describe each screen below in enough detail that a developer could implement it pixel-accurately using the tokens from Sections 1 and 2, and a designer could draw it in Figma in one pass. For each screen provide:

1. **Layout structure** — exact component hierarchy (NavigationBar, ScrollView, sticky header, bottom sheet, etc.)
2. **Component inventory** — every UI component on screen with its variant, token references, and dimensions
3. **Spacing & grid** — base unit (suggest 4 px), padding, gutters, safe areas
4. **Interactive states** — what changes on press, focus, swipe, long-press
5. **Dark mode delta** — only call out what changes; don't repeat the full spec

### Screens to specify

**1. Home Feed**
Shows: recommended bars (horizontal scroll), upcoming raids the user is attending (vertical cards), friends' activity feed. Include a sticky top bar with greeting text, notification bell, and avatar. Floating action button to start a new raid.

**2. Bar Detail**
Shows: full-bleed hero photo with gradient overlay, back button, share/bookmark icons, bar name + rating, quick-stat chips (price category, vibe tags, distance), tabbed content area (Info / Reviews / Raids at this bar), sticky bottom CTA bar with "Add to Favorites" and "Plan a Raid" buttons.

**3. Chat — Conversation**
Shows: conversation list header (group name, participant avatars), message bubbles (sent right / received left), reactions bar, reply-preview strip, input toolbar with emoji, attach, and send. Indicate how the typing indicator looks.

**4. Split Room**
Shows: receipt header (bar name, total amount, status pill), participant strip with avatar + color chip + subtotal, item list (item name, unit price, quantity, assignment chips per claimant), "Ready" button sticky at bottom, progress banner when all participants are ready.

**5. Profile**
Shows: large avatar with race-colored ring, username, fantasy race badge with race icon, XP bar, stat row (check-ins, raids, friends), achievements section (locked + unlocked states), favorite bars horizontal strip, edit profile button.

---

## Section 4 — Component Library Style Guide

For each component below, describe: purpose, variants/states, exact token usage (fill, border, text, shadow), border radius, padding, and any animation spec (duration, easing, property).

### Components

**Button**
Variants: Primary (filled `$brandPrimary`), Secondary (outlined), Ghost (text only), Danger (filled `$error`), Gold CTA (filled `$accentGold`, used only for dice roll and "Kind Soul" reveal). Sizes: Large (48 dp), Medium (40 dp), Small (32 dp). Loading state: spinner replaces label; disabled state: opacity 40%.

**Card**
Variants: Bar card (image left, info right, rating chip top-right), Raid card (horizontal timeline strip, RSVP pills), Activity card (avatar left, event text, timestamp). Elevation: 1 dp shadow with `$borderDefault` for light mode; no shadow + subtle border for dark mode.

**BottomSheet / Modal**
Handle bar at top, `$bgElevated` fill, border radius 20 dp top corners, backdrop `rgba(0,0,0,0.5)`. Snap points: 40 %, 70 %, full screen. Animation: spring (stiffness 300, damping 30).

**Tab Bar**
4 primary tabs: Home, Bars, Friends, Profile. Active tab: icon fills `$brandPrimary`, label `$labelM` in `$brandPrimary`. Inactive: `$textSecondary`. Badge on Friends tab for pending requests. Background `$bgCard`, top border `$borderDefault`.

**Avatar**
Sizes: XS (24 dp), S (32 dp), M (48 dp), L (64 dp), XL (96 dp). Variants: photo, initials fallback (bg `$accentGoldSubtle`, text `$accentGoldText`), race ring (3 dp ring in `$race{Race}Bg`). Stacked group: -8 dp offset, up to 5 visible + "+N" overflow chip.

**Chip / Pill**
Variants: Vibe tag (outlined, `$borderDefault`), RSVP status (filled — Going `$success`, Maybe `$warning`, Declined `$error`), Race badge (filled `$race{Race}Bg`), Price tier (outlined, `$textSecondary`). Border radius: fully rounded (999 dp). Font: `$labelS`.

**Rating Star**
Filled star: `$accentGold`. Empty star: `$borderDefault`. Half star: gradient split. Size: 16 dp inline, 24 dp on detail page.

**Input**
Background `$bgInput`, border `$borderDefault`, focus border `$borderFocus` (2 dp), border radius 12 dp. Label floats above on focus. Error state: border `$error`, helper text in `$error`. Font: `$bodyM`.

**Toast / Snackbar**
Bottom-anchored, 16 dp from safe area. Variants: success (left bar `$success`), warning (`$warning`), error (`$error`), info (`$brandPrimarySubtle`). Auto-dismiss 3 s. Slide up + fade in (200 ms ease-out), slide down + fade out (150 ms).

**Dice Roll Animation**
A large D20 polygon rendered in `$accentGold` with a shadow glow. On roll: 600 ms tumble rotation (ease-in-out), then 300 ms settle bounce, then the number `$displayXL` fades in. The loser's avatar pulses red (`$error`) for 400 ms; the "Kind Soul" crown icon drops in from above with a spring.

---

## Competitive reference

Design at or above the visual quality of: **Untappd** (bar social), **Foursquare City Guide** (venue discovery), **Splitwise** (bill splitting), **Discord** (real-time chat). The fantasy/tavern skin is a differentiator — lean into it, but never at the cost of usability or legibility. A first-time user should understand what the app does within 10 seconds of seeing the Home screen.

---

## Deliverable format

Return your answer as structured markdown with clear `##` headings for each section. For the color tokens, use a markdown table. For the typography tokens, use a markdown table. For the screen mockups, use numbered lists with nested bullets. For the component guide, use one `###` subsection per component.

Do not include placeholder text — every value must be a real design decision you are committing to.
