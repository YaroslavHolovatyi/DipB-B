/**
 * Beer & Beverages — Tamagui Configuration
 *
 * We extend @tamagui/config/v3 (the official "batteries-included" base) and
 * overlay our B&B brand tokens on top.  Screen-level layouts should use the
 * exported `colors` from ./colors.ts so they don't depend on Tamagui at all,
 * but shared UI components (Button, Card, Input …) should reference these
 * tokens for consistent theming.
 */
import { config as baseConfig } from '@tamagui/config/v3';
import { createTamagui, createTokens } from 'tamagui';

// ── Custom color scale for B&B ────────────────────────────────────────────────
const bbColors = {
  // Brand
  brandPrimary1:  '#EEF2FF',
  brandPrimary2:  '#E0E7FF',
  brandPrimary3:  '#C7D2FE',
  brandPrimary4:  '#A5B4FC',
  brandPrimary5:  '#818CF8',
  brandPrimary6:  '#6366F1',
  brandPrimary7:  '#4F46E5',
  brandPrimary8:  '#4338CA',
  brandPrimary9:  '#3730A3',
  brandPrimary10: '#312E81',

  // Gold
  gold1: '#FFFBEB',
  gold2: '#FEF3C7',
  gold3: '#FDE68A',
  gold4: '#FCD34D',
  gold5: '#FBBF24',
  gold6: '#F59E0B',
  gold7: '#D97706',
  gold8: '#B45309',
  gold9: '#92400E',
  gold10: '#78350F',

  // Emerald (secondary accent)
  emerald6: '#10B981',
  emerald7: '#059669',
};

// ── Tokens ────────────────────────────────────────────────────────────────────
const tokens = createTokens({
  ...baseConfig.tokens,
  color: {
    ...baseConfig.tokens.color,
    ...bbColors,
  },
  // Override border-radius scale to match our 4-pt grid
  radius: {
    0:   0,
    1:   4,
    2:   8,
    3:   12,
    4:   16,
    5:   20,
    6:   24,
    true: 12,
    full: 9999,
  },
  // Override space scale (multiples of 4)
  space: {
    ...baseConfig.tokens.space,
    '$0.5': 2,
    '$1':   4,
    '$1.5': 6,
    '$2':   8,
    '$2.5': 10,
    '$3':   12,
    '$3.5': 14,
    '$4':   16,
    '$5':   20,
    '$6':   24,
    '$7':   28,
    '$8':   32,
    '$10':  40,
    '$12':  48,
    '$16':  64,
    true:   16,
  },
});

// ── Light Theme ───────────────────────────────────────────────────────────────
const lightTheme = {
  ...baseConfig.themes.light,
  background:           '#F9FAFB',
  backgroundHover:      '#F3F4F6',
  backgroundPress:      '#E5E7EB',
  backgroundFocus:      '#E5E7EB',
  backgroundStrong:     '#FFFFFF',
  backgroundTransparent:'transparent',
  color:                '#111827',
  colorHover:           '#1F2937',
  colorPress:           '#374151',
  colorFocus:           '#374151',
  colorTransparent:     'transparent',
  borderColor:          '#E5E7EB',
  borderColorHover:     '#D1D5DB',
  borderColorFocus:     '#6366F1',
  borderColorPress:     '#6366F1',
  placeholderColor:     '#9CA3AF',
  // B&B brand overrides
  primary:  '#6366F1',
  gold:     '#F59E0B',
  success:  '#059669',
  warning:  '#D97706',
  danger:   '#DC2626',
};

// ── Dark Theme ────────────────────────────────────────────────────────────────
const darkTheme = {
  ...baseConfig.themes.dark,
  background:           '#0D0D1A',
  backgroundHover:      '#13132B',
  backgroundPress:      '#1A1A35',
  backgroundFocus:      '#1A1A35',
  backgroundStrong:     '#13132B',
  backgroundTransparent:'transparent',
  color:                '#F1F5F9',
  colorHover:           '#FFFFFF',
  colorPress:           '#CBD5E1',
  colorFocus:           '#CBD5E1',
  colorTransparent:     'transparent',
  borderColor:          '#2D2D4A',
  borderColorHover:     '#3D3D5A',
  borderColorFocus:     '#818CF8',
  borderColorPress:     '#818CF8',
  placeholderColor:     '#475569',
  // B&B brand overrides
  primary:  '#818CF8',
  gold:     '#F59E0B',
  success:  '#10B981',
  warning:  '#FBBF24',
  danger:   '#F87171',
};

// ── Assemble Config ───────────────────────────────────────────────────────────
export const tamaguiConfig = createTamagui({
  ...baseConfig,
  tokens,
  themes: {
    ...baseConfig.themes,
    light: lightTheme,
    dark:  darkTheme,
  },
  fonts: {
    ...baseConfig.fonts,
    heading: {
      family: 'Fraunces_700Bold',
      size: baseConfig.fonts.body?.size ?? {},
      lineHeight: baseConfig.fonts.body?.lineHeight ?? {},
      weight: { true: '700' },
      letterSpacing: { true: -0.5 },
      face: {
        700: { normal: 'Fraunces_700Bold' },
        600: { normal: 'Fraunces_600SemiBold' },
      },
    },
    body: {
      family: 'PlusJakartaSans_400Regular',
      size: baseConfig.fonts.body?.size ?? {},
      lineHeight: baseConfig.fonts.body?.lineHeight ?? {},
      weight: { true: '400' },
      letterSpacing: { true: 0 },
      face: {
        400: { normal: 'PlusJakartaSans_400Regular' },
        600: { normal: 'PlusJakartaSans_600SemiBold' },
        700: { normal: 'PlusJakartaSans_700Bold' },
      },
    },
    mono: {
      family: 'JetBrainsMono_500Medium',
      size: baseConfig.fonts.body?.size ?? {},
      lineHeight: baseConfig.fonts.body?.lineHeight ?? {},
      weight: { true: '500' },
      letterSpacing: { true: -0.5 },
      face: {
        500: { normal: 'JetBrainsMono_500Medium' },
        700: { normal: 'JetBrainsMono_700Bold' },
      },
    },
  },
  settings: {
    allowedStyleValues: 'somewhat-strict',
    autocompleteSpecificTokens: true,
  },
});

export default tamaguiConfig;

// Required for typed Tamagui usage
export type Conf = typeof tamaguiConfig;
declare module 'tamagui' {
  interface TamaguiCustomConfig extends Conf {}
}
