/**
 * Beer & Beverages — Design System Color Tokens
 * Derived from the DESIGN_PROMPT.md spec.
 * Use these constants anywhere StyleSheet is preferred over Tamagui components.
 */

export const colors = {
  // ── Backgrounds — parchment (light) / aged wood (dark) ───
  bgBase:     '#F1E5C9',
  bgCard:     '#FAF2DC',
  bgElevated: '#FFF8E7',
  bgInput:    '#E7D8B4',

  bgBaseDark:     '#1B130B',
  bgCardDark:     '#2A1E11',
  bgElevatedDark: '#352616',
  bgInputDark:    '#2E2113',

  // ── Brand / Primary — tavern amber/bronze ────────────────
  brandPrimary:       '#B4571C',
  brandPrimaryHover:  '#8F4214',
  brandPrimarySubtle: '#F3DDBE',

  // ── Fantasy Accent — Gold ────────────────────────────────
  accentGold:       '#D99A1C',
  accentGoldSubtle: '#F6E4BB',
  accentGoldText:   '#825311',

  // ── Secondary Accent — Herb / Dragon Green ───────────────
  accentSecondary:       '#4E7A45',
  accentSecondarySubtle: '#DCE7CB',

  // ── Semantic ─────────────────────────────────────────────
  success:        '#3F7A3F',
  successSubtle:  '#DCE7CB',
  warning:        '#B5781A',
  warningSubtle:  '#F6E4BB',
  error:          '#9B2C20',
  errorSubtle:    '#F0D9CF',

  // ── Text — ink on parchment ──────────────────────────────
  textPrimary:    '#3A2A18',
  textSecondary:  '#6E5733',
  textDisabled:   '#9C8A66',
  textOnBrand:    '#FFF8E7',
  textOnGold:     '#3A2A18',

  // Text — Dark mode (parchment on wood)
  textPrimaryDark:   '#EFE2C6',
  textSecondaryDark: '#BBA784',
  textDisabledDark:  '#7C6B4C',

  // ── Borders ──────────────────────────────────────────────
  borderDefault: '#D9C49A',
  borderStrong:  '#C2A871',
  borderFocus:   '#B4571C',

  borderDefaultDark: '#4A3724',
  borderStrongDark:  '#5E4730',

  // ── Gamification — Race colors ───────────────────────────
  raceHumanBg:    '#DBEAFE',  raceHumanText:    '#1E40AF',
  raceElfBg:      '#DCFCE7',  raceElfText:      '#166534',
  raceDwarfBg:    '#FFEDD5',  raceDwarfText:    '#9A3412',
  raceOrcBg:      '#ECFCCB',  raceOrcText:      '#4D7C0F',
  raceHalflingBg: '#FEE2E2',  raceHalflingText: '#991B1B',
  raceGnomeBg:    '#F3E8FF',  raceGnomeText:    '#6B21A8',

  // ── Leaderboard Tiers ────────────────────────────────────
  tierGold:   '#F59E0B',
  tierSilver: '#94A3B8',
  tierBronze: '#C2763A',

  // ── Welcome Screen (always dark tavern) ──────────────────
  welcomeBg:      '#140D07',
  welcomeGradientStart: '#140D07',
  welcomeGradientMid:   '#241606',
  welcomeGradientEnd:   '#3A2410',
} as const;

export type ColorToken = keyof typeof colors;
