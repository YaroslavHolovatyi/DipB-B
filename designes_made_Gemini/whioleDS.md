## Section 1 — Color Palette & Design Tokens

This color system balances a modern, vibrant social UX with rich, warm tavern undertones. The primary palette leans on an energetic "Arcane Indigo" to feel distinctly digital and modern, while the accents bring in the atmospheric candlelight and gold of a fantasy tavern. 

| Tamagui Token | Light Mode Hex | Dark Mode Hex | Usage |
| :--- | :--- | :--- | :--- |
| **Background Surfaces** | | | |
| `$bgBase` | `#F9FAFB` | `#121214` | Main app background; parchment-white in light mode, deep charcoal in dark mode. |
| `$bgCard` | `#FFFFFF` | `#18181B` | Surface for bar cards, raid listings, and profile panels. |
| `$bgElevated` | `#FFFFFF` | `#27272A` | Floating elements like bottom sheets, modals, and dropdowns. |
| `$bgInput` | `#F3F4F6` | `#27272A` | Background fill for search bars and chat text inputs. |
| **Brand / Primary** | | | |
| `$brandPrimary` | `#6366F1` | `#818CF8` | Main CTA buttons, active tab icons, and primary interactions. |
| `$brandPrimaryHover` | `#4F46E5` | `#6366F1` | Pressed or active state for primary brand elements. |
| `$brandPrimarySubtle` | `#E0E7FF` | `#312E81` | Tinted background for selected chips, unread chat indicators. |
| **Fantasy Accent (Gold)** | | | |
| `$accentGold` | `#F59E0B` | `#FBBF24` | Dice roll results, "Kind Soul" crown, achievement badges, and raid timers. |
| `$accentGoldSubtle` | `#FEF3C7` | `#78350F` | Glowing background behind gold icons or highlighted leaderboard rows. |
| `$accentGoldText` | `#B45309` | `#FDE68A` | High-contrast gold text for labels sitting on `$bgBase` or `$bgCard`. |
| **Secondary Accent** | | | |
| `$accentSecondary` | `#10B981` | `#34D399` | "Emerald" accent for Active Raid indicators, Party badges, and level-ups. |
| `$accentSecondarySubtle`| `#D1FAE5` | `#064E3B` | Soft background for secondary accent chips. |
| **Semantic** | | | |
| `$success` | `#059669` | `#10B981` | RSVP "Going", assignment confirmed in split room, successful payment. |
| `$successSubtle` | `#D1FAE5` | `#022C22` | Background for success toasts and success state pills. |
| `$warning` | `#D97706` | `#FBBF24` | RSVP "Maybe", unclaimed receipt items, expiring raid sessions. |
| `$warningSubtle` | `#FEF3C7` | `#451A03` | Background for warning banners and pending states. |
| `$error` | `#DC2626` | `#F87171` | Validation errors, destructive actions, and RSVP "Declined". |
| `$errorSubtle` | `#FEE2E2` | `#450A0A` | Background for error toasts and declined state pills. |
| **Text** | | | |
| `$textPrimary` | `#111827` | `#F9FAFB` | Main headings, primary form labels, and critical data points. |
| `$textSecondary` | `#6B7280` | `#A1A1AA` | Subtext, timestamps, distances, and secondary UI labels. |
| `$textDisabled` | `#9CA3AF` | `#52525B` | Disabled button text and empty state illustrations. |
| `$textOnBrand` | `#FFFFFF` | `#FFFFFF` | Text or icons resting directly on `$brandPrimary` fills. |
| `$textOnAccentGold` | `#111827` | `#18181B` | Text resting directly on `$accentGold` fills. |
| **Borders & Dividers** | | | |
| `$borderDefault` | `#E5E7EB` | `#27272A` | Standard dividers between list items and subtle card borders. |
| `$borderStrong` | `#D1D5DB` | `#3F3F46` | Prominent borders for emphasized sections or floating headers. |
| `$borderFocus` | `#6366F1` | `#818CF8` | Input focus rings and active keyboard navigation states. |
| **Gamification (Races & Tiers)**| | | |
| `$raceHumanBg` | `#DBEAFE` | `#1E3A8A` | Background for Human race avatar rings and badges. |
| `$raceHumanText` | `#1E40AF` | `#93C5FD` | Foreground icon/text for Human race elements. |
| `$raceElfBg` | `#DCFCE7` | `#14532D` | Background for Elf race avatar rings and badges. |
| `$raceElfText` | `#166534` | `#86EFAC` | Foreground icon/text for Elf race elements. |
| `$raceDwarfBg` | `#FFEDD5` | `#7C2D12` | Background for Dwarf race avatar rings and badges. |
| `$raceDwarfText` | `#9A3412` | `#FDBA74` | Foreground icon/text for Dwarf race elements. |
| `$raceOrcBg` | `#ECFCCB` | `#3F6212` | Background for Orc race avatar rings and badges. |
| `$raceOrcText` | `#4D7C0F` | `#BEF264` | Foreground icon/text for Orc race elements. |
| `$raceHalflingBg` | `#FEF08A` | `#854D0E` | Background for Halfling race avatar rings and badges. |
| `$raceHalflingText`| `#A16207` | `#FDE047` | Foreground icon/text for Halfling race elements. |
| `$raceGnomeBg` | `#F3E8FF` | `#581C87` | Background for Gnome race avatar rings and badges. |
| `$raceGnomeText` | `#7E22CE` | `#D8B4FE` | Foreground icon/text for Gnome race elements. |
| `$tierGold` | `#F59E0B` | `#FBBF24` | First place leaderboard indicator and premium achievements. |
| `$tierSilver` | `#94A3B8` | `#CBD5E1` | Second place leaderboard indicator. |
| `$tierBronze` | `#B45309` | `#D97706` | Third place leaderboard indicator. |

---

## Section 2 — Typography System

The typography relies on Google Fonts available via `@expo-google-fonts`. We pair **Fraunces** (a characterful, slightly robust serif with high x-height) to evoke a modern tavern feel, with **Plus Jakarta Sans** (clean, geometric sans-serif) for high legibility in dense UI like chats and split rooms. **JetBrains Mono** is used for numerals to guarantee perfect tabular alignment for dynamic prices and dice rolls.

| Tamagui Token | Family | Wgt | Size | Line Ht | Track | Usage |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `$displayXL` | `JetBrains Mono` | 800 | 56px | 64px | -2% | D20 roll results, massive splash numbers. |
| `$displayL` | `Fraunces` | 700 | 40px | 48px | -1% | Onboarding screen titles, heroic callouts. |
| `$headingXL` | `Fraunces` | 700 | 32px | 40px | 0% | Bar names on detail pages, specific Raid titles. |
| `$headingL` | `Fraunces` | 600 | 24px | 32px | 0% | Primary section headers (e.g., "Upcoming Raids"). |
| `$headingM` | `Plus Jakarta Sans`| 700 | 20px | 28px | 0% | Card titles, username on profile screens. |
| `$headingS` | `Plus Jakarta Sans`| 600 | 16px | 24px | +1% | Subheadings, group chat names in lists. |
| `$bodyL` | `Plus Jakarta Sans`| 400 | 16px | 24px | 0% | Chat message bodies, expansive UI text. |
| `$bodyM` | `Plus Jakarta Sans`| 400 | 14px | 20px | 0% | List item descriptions, review body text. |
| `$bodyS` | `Plus Jakarta Sans`| 400 | 12px | 16px | +2% | Secondary labels, timestamp captions, distances. |
| `$labelL` | `Plus Jakarta Sans`| 700 | 16px | 20px | +1% | Primary button labels, vital UI actions. |
| `$labelM` | `Plus Jakarta Sans`| 600 | 14px | 16px | +2% | Tab labels, chip text, categorical filters. |
| `$labelS` | `Plus Jakarta Sans`| 600 | 12px | 16px | +3% | Badge text, race tags, small indicators. |
| `$numericL` | `JetBrains Mono` | 700 | 24px | 32px | 0% | Receipt totals, final split amounts. |
| `$numericM` | `JetBrains Mono` | 500 | 16px | 24px | 0% | Individual item prices in the split room. |
| `$numericS` | `JetBrains Mono` | 500 | 14px | 20px | 0% | Distance metrics (e.g., "1.2 km"), subtotals. |

---

## Section 3 — Key Screen Mockups

### 1. Home Feed
1.  **Layout structure**
    * `SafeAreaView` > `ScrollView` (vertical).
    * Sticky Header (blur backdrop): `XStack` with User Greeting, Notification Bell (`$brandPrimary` badge), and Mini Avatar.
    * Horizontal `ScrollView`: "Recommended Taverns".
    * Vertical `YStack`: "Upcoming Raids".
    * Vertical `YStack`: "Friends' Activity".
    * Absolute Positioned `FloatingActionButton` (bottom right).
2.  **Component inventory**
    * **Header:** Text (`$headingS`), Icon Button (Bell), Avatar (Size S, with `$raceDwarfBg` ring).
    * **Recommended:** Bar Cards (Horizontal variant, 240dp width). Features images of places like "Lviv Craft Haven" or "Bukovel Peak Inn".
    * **Upcoming Raids:** Raid Cards (Vertical variant, full width minus padding).
    * **Activity:** Activity Cards (List variant, transparent background).
    * **FAB:** Large (56dp), Pill shape, Fill `$accentGold`, Icon "Swords crossed".
3.  **Spacing & grid**
    * Base grid: 4px.
    * Screen horizontal padding: 16dp.
    * Gutter between horizontal cards: 12dp.
    * Section vertical spacing (`YStack` gap): 32dp.
4.  **Interactive states**
    * Pressing a Raid Card scales it down to 0.97 (spring animation) before navigating.
    * Scrolling down applies a bottom border (`$borderDefault`) and blur to the sticky header.
5.  **Dark mode delta**
    * Sticky header background shifts from `rgba(255,255,255,0.8)` to `rgba(18,18,20,0.8)`. 
    * Shadows on horizontal cards are removed; replaced with `$borderDefault` outlines.

### 2. Bar Detail
1.  **Layout structure**
    * `ScrollView` with parallax header image.
    * Absolute Top `XStack`: Back button (left), Bookmark/Share (right).
    * Main Content `YStack` (border radius top 24dp, overlaps image).
    * Sticky Bottom `XStack` Bar (Safe area bottom + 16dp).
2.  **Component inventory**
    * **Hero:** Image (Height 300dp) with linear gradient overlay (Transparent to `$bgBase`).
    * **Header Info:** Text (`$headingXL`), Rating Star component (24dp), Text (`$bodyS`).
    * **Quick Stats:** `XStack` containing Chips (Price `$$`, Vibe "Cozy", Distance "0.8km").
    * **Tabs:** Custom Tab Bar component (Info / Reviews / Raids).
    * **Bottom Bar:** Button (Secondary, "Add to Favorites"), Button (Primary, "Plan a Raid").
3.  **Spacing & grid**
    * Main content overlaps hero image by -24dp.
    * Internal content padding: 20dp horizontal, 24dp vertical gap between sections.
    * Bottom bar padding: 16dp horizontal, gap 12dp between buttons.
4.  **Interactive states**
    * Hero image scales up on over-scroll (pull down).
    * "Add to Favorites" triggers a haptic success bump and icon fills with `$accentGold`.
5.  **Dark mode delta**
    * Hero image gradient overlay fades to `#121214`.
    * Bottom sticky bar gets a subtle top border (`$borderStrong`) to separate from dark content.

### 3. Chat — Conversation
1.  **Layout structure**
    * `SafeAreaView`.
    * Top `NavigationBar`: Standard back chevron, group name, avatar stack.
    * `KeyboardAvoidingView` > `FlatList` (inverted).
    * Bottom Input Toolbar `XStack`.
2.  **Component inventory**
    * **Header:** Text (`$headingS`), Avatar Stack (Group up to 3).
    * **Message Bubbles:** `YStack`. Right (sent): fill `$brandPrimary`, text `$textOnBrand`. Left (received): fill `$bgCard`, text `$textPrimary`. 
    * **Typing Indicator:** Left-aligned bubble with 3 animated dot icons.
    * **Input Toolbar:** Input Field component, Icon Buttons (Emoji, Attach, Send).
3.  **Spacing & grid**
    * Message bubble padding: 12dp horizontal, 10dp vertical. Border radius 16dp (with 2dp radius on the tail corner).
    * Message gap: 4dp (same user), 16dp (different user).
4.  **Interactive states**
    * Long-press message bubble: Triggers bottom sheet with Emoji reactions and "Reply" action.
    * Send button opacity shifts from 40% (disabled) to 100% (enabled) when text length > 0.
5.  **Dark mode delta**
    * Received messages shift from `$bgCard` (White) to `#27272A` (`$bgElevated`).

### 4. Split Room
1.  **Layout structure**
    * `SafeAreaView` > `YStack`.
    * Header `YStack`: Bar name, total, dynamic status pill.
    * Horizontal `ScrollView`: Participant strip.
    * `ScrollView`: Itemized receipt list.
    * Sticky Bottom `YStack`: "Ready" Button, dynamic progress text.
2.  **Component inventory**
    * **Header:** Text (`$headingM`), Text (`$numericL` for total), Pill ("Unsettled" `$warning`).
    * **Participant Strip:** Avatar components (Size M) with active rings in `$brandPrimary`. Subtotal Text (`$numericS`).
    * **Item List Row:** `XStack` with Item Name Text (`$bodyM`), Price Text (`$numericM`), and overlapping Avatar XS chips indicating who claims it.
    * **Bottom CTA:** Button (Primary, Large, "Roll D20 to Pay").
3.  **Spacing & grid**
    * Header padding: 24dp top, 20dp horizontal.
    * Item row padding: 16dp vertical (border bottom `$borderDefault`).
    * Participant strip gap: 16dp.
4.  **Interactive states**
    * Tap item row: Adds your avatar chip to the item, recalculates live subtotals.
    * Tap "Roll D20": Triggers fullscreen Dice Roll Animation overlay.
5.  **Dark mode delta**
    * Item row border bottom changes to `$borderStrong` for better visibility against dark backgrounds.

### 5. Profile
1.  **Layout structure**
    * `ScrollView`.
    * Top `YStack` (Centered): Avatar, Name, Race Badge.
    * `XStack`: XP Bar.
    * `XStack`: Stat row (3 columns).
    * `YStack`: Achievements grid (2 columns).
    * Horizontal `ScrollView`: Favorite Bars.
2.  **Component inventory**
    * **Identity:** Avatar (Size XL, e.g., `$raceElfBg` ring), Text (`$headingM`), Chip (Race Badge, filled `$raceElfBg`).
    * **XP Bar:** Custom progress bar. Track `$bgElevated`, Fill `$accentSecondary`.
    * **Stats:** `YStack` with Numeric (`$numericM`) over Text (`$bodyS`).
    * **Achievements:** Card components (Square aspect ratio), lock icon for unearned (`$textDisabled`).
3.  **Spacing & grid**
    * Avatar top margin: 32dp.
    * Stat row padding: 20dp, separated by vertical dividers (`$borderDefault`).
    * Grid gap (Achievements): 16dp.
4.  **Interactive states**
    * Pressing an unlocked achievement triggers a 3D flip card animation showing unlock date and details.
5.  **Dark mode delta**
    * Locked achievements lower opacity to 30% against `$bgBase` to recede visually.

---

## Section 4 — Component Library Style Guide

### Button
* **Purpose:** Primary interactive elements for form submission, navigation, and modal triggers.
* **Variants & States:**
    * *Primary:* Fill `$brandPrimary`, Text `$textOnBrand`.
    * *Secondary:* Fill transparent, Border 2dp `$borderStrong`, Text `$textPrimary`.
    * *Ghost:* Fill transparent, Text `$textSecondary` (Hover/Press: Fill `$bgElevated`).
    * *Danger:* Fill `$error`, Text `$textOnBrand`.
    * *Gold CTA:* Fill `$accentGold`, Text `$textOnAccentGold`. Used exclusively for "Roll D20".
* **Dimensions:** Large (48dp height, px 24dp), Medium (40dp height, px 16dp), Small (32dp height, px 12dp). Fully rounded edges (radius 999dp).
* **Tokens & Animation:** Disabled state opacity 40%. Press state scales to 0.95 with a 150ms ease-out spring. Loading state swaps label for a `ActivityIndicator` in `$textOnBrand`.

### Card
* **Purpose:** Grouping distinct pieces of interactive content (bars, raids, activity).
* **Variants & States:**
    * *Bar Card:* Horizontal layout. Left fixed-width image (100dp), right content flex area. 
    * *Raid Card:* Vertical layout. Header image, title, RSVP chips below.
* **Tokens & Padding:** Fill `$bgCard`. Padding 16dp (for text areas). Border radius 16dp.
* **Elevation:** Light mode: `shadowColor: #000`, `shadowOpacity: 0.05`, `shadowRadius: 8`, `shadowOffset: { height: 2 }`. Dark mode: No shadow, border 1dp `$borderDefault`.

### BottomSheet / Modal
* **Purpose:** Contextual tasks (planning a raid, selecting a race) without losing screen context.
* **Tokens & Padding:** Fill `$bgElevated`. Top left/right border radius 24dp. Top drag handle: width 40dp, height 4dp, fill `$borderStrong`, top margin 12dp. Backdrop: `rgba(0,0,0,0.5)`.
* **Animation:** Tamagui/Reanimated Spring. Stiffness 300, Damping 30. Snaps dynamically to 40%, 70%, or 100%.

### Tab Bar
* **Purpose:** Primary bottom-level application navigation.
* **Variants & States:** 4 Tabs (Home, Bars, Friends, Profile). 
* **Tokens & Padding:** Background `$bgCard`, Top border 1dp `$borderDefault`. Height 80dp (including safe area).
* **Interactions:** Active tab: Icon fills with `$brandPrimary`, text becomes visible in `$labelM` color `$brandPrimary`. Inactive: Icon outlines in `$textSecondary`, text hidden. Badge on Friends uses `$error` background.

### Avatar
* **Purpose:** Representing users, both visually and via gamified fantasy rings.
* **Variants & Sizes:** XS (24dp), S (32dp), M (48dp), L (64dp), XL (96dp). 
* **Tokens:** Image variant (clip to circle). Initials variant (Fill `$accentGoldSubtle`, Text `$accentGoldText`). Race Ring variant applies a 3dp padding and an outer border matching `$race{Race}Bg`.
* **Stacked Group:** Negative margin `-8dp` on consecutive avatars. Max 5 visible, final avatar is an Initials variant reading `+N`.

### Chip / Pill
* **Purpose:** Metadata tags, RSVP statuses, and dynamic filters.
* **Variants & States:**
    * *RSVP:* Going (Fill `$success`, Text `$textOnBrand`), Maybe (Fill `$warning`, Text `$textOnAccentGold`), Declined (Fill `$error`, Text `$textOnBrand`).
    * *Race Badge:* Fill `$race{Race}Bg`, Text `$race{Race}Text`.
    * *Vibe Tag:* Fill transparent, Border 1dp `$borderDefault`, Text `$textSecondary`.
* **Tokens & Padding:** Height 24dp, horizontal padding 10dp. Border radius 999dp. Typography `$labelS`.

### Rating Star
* **Purpose:** Quick visual read of venue reviews.
* **Tokens:** Filled `$accentGold`. Empty `$borderDefault`.
* **Dimensions:** Inline (16dp, 2dp gap). Detail page (24dp, 4dp gap).

### Input
* **Purpose:** Text entry for search, chat, and profile editing.
* **Tokens & States:** Background `$bgInput`. Default border 1dp transparent. Focus border 2dp `$borderFocus`. Error state border 2dp `$error`.
* **Dimensions:** Height 48dp, padding horizontal 16dp. Border radius 12dp. Typography `$bodyM`.
* **Animation:** Label transitions from `$bodyM` (centered) to `$bodyS` (floated top left) over 200ms ease-out on focus.

### Toast / Snackbar
* **Purpose:** Transient system feedback.
* **Tokens & Layout:** Absolute bottom, 16dp above safe area. Fill `$bgElevated`. Border radius 12dp. Left decorative border (4dp width, mapped to semantic color: `$success`, `$warning`, `$error`). Text `$bodyM`.
* **Animation:** Enter: Slide up 20dp + Fade in (200ms ease-out). Exit: Slide down 10dp + Fade out (150ms ease-in). Auto-dismiss after 3000ms.

### Dice Roll Animation
* **Purpose:** The core gamification mechanic for the "Kind Soul" bill-splitting feature.
* **Tokens:** D20 polygon rendered in 3D or SVG, fill `$accentGold`. Result text `$displayXL` (`JetBrains Mono`). Loser pulse overlay `$error`.
* **Animation Spec:** 1.  **Roll:** D20 tumble rotation (CSS/Reanimated `rotate` and `scale`) for 600ms (ease-in-out).
    2.  **Settle:** 300ms spring bounce (scale 1.2 to 1.0) as the die lands.
    3.  **Reveal:** `$displayXL` number fades in (150ms).
    4.  **Consequence:** Loser avatar scales up 1.1x and pulses `$error` border for 400ms. "Kind Soul" crown drops from `-100px` Y-axis with a heavy spring (Stiffness 200, Damping 12) onto the loser's avatar.