/**
 * Beer & Beverages — Design System Color Tokens
 * Derived from the DESIGN_PROMPT.md spec.
 * Use these constants anywhere StyleSheet is preferred over Tamagui components.
 */

export const colors = {
  // ── Backgrounds ──────────────────────────────────────────
  bgBase:     '#F9FAFB',
  bgCard:     '#FFFFFF',
  bgElevated: '#FFFFFF',
  bgInput:    '#F3F4F6',

  bgBaseDark:     '#0D0D1A',
  bgCardDark:     '#13132B',
  bgElevatedDark: '#1A1A35',
  bgInputDark:    '#1E1E38',

  // ── Brand / Primary ──────────────────────────────────────
  brandPrimary:       '#6366F1',
  brandPrimaryHover:  '#4F46E5',
  brandPrimarySubtle: '#E0E7FF',

  // ── Fantasy Accent — Gold ────────────────────────────────
  accentGold:       '#F59E0B',
  accentGoldSubtle: '#FEF3C7',
  accentGoldText:   '#B45309',

  // ── Secondary Accent — Emerald ───────────────────────────
  accentSecondary:       '#10B981',
  accentSecondarySubtle: '#D1FAE5',

  // ── Semantic ─────────────────────────────────────────────
  success:        '#059669',
  successSubtle:  '#D1FAE5',
  warning:        '#D97706',
  warningSubtle:  '#FEF3C7',
  error:          '#DC2626',
  errorSubtle:    '#FEE2E2',

  // ── Text ─────────────────────────────────────────────────
  textPrimary:    '#111827',
  textSecondary:  '#6B7280',
  textDisabled:   '#9CA3AF',
  textOnBrand:    '#FFFFFF',
  textOnGold:     '#111827',

  // Text — Dark mode
  textPrimaryDark:   '#F1F5F9',
  textSecondaryDark: '#94A3B8',
  textDisabledDark:  '#475569',

  // ── Borders ──────────────────────────────────────────────
  borderDefault: '#E5E7EB',
  borderStrong:  '#D1D5DB',
  borderFocus:   '#6366F1',

  borderDefaultDark: '#2D2D4A',
  borderStrongDark:  '#3D3D5A',

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

  // ── Welcome Screen (always dark) ─────────────────────────
  welcomeBg:      '#0A0A1A',
  welcomeGradientStart: '#0A0A1A',
  welcomeGradientMid:   '#120E30',
  welcomeGradientEnd:   '#1E0E3E',
} as const;

export type ColorToken = keyof typeof colors;
