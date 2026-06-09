/**
 * Convenience re-exports of frequently used style constants.
 * Import as:  import { C, F } from '../theme/styleHelpers';
 */
export { colors as C } from './colors';

/** Font family name constants — must match the keys passed to useFonts() */
export const F = {
  headingBold:     'Fraunces_700Bold',
  headingSemi:     'Fraunces_600SemiBold',
  bodyRegular:     'PlusJakartaSans_400Regular',
  bodySemiBold:    'PlusJakartaSans_600SemiBold',
  bodyBold:        'PlusJakartaSans_700Bold',
  monoMedium:      'JetBrainsMono_500Medium',
  monoBold:        'JetBrainsMono_700Bold',
} as const;
