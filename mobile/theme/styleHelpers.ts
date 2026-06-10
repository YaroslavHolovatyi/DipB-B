/**
 * Convenience re-exports of frequently used style constants.
 * Import as:  import { C, F } from '../theme/styleHelpers';
 */
export { colors as C } from './colors';

/** Font family name constants — must match the keys passed to useFonts() */
export const F = {
  // Headings use MedievalSharp to match the fantasy-tavern icon lettering.
  // MedievalSharp ships a single weight, so bold/semi map to the same family.
  headingBold:     'MedievalSharp_400Regular',
  headingSemi:     'MedievalSharp_400Regular',
  bodyRegular:     'PlusJakartaSans_400Regular',
  bodySemiBold:    'PlusJakartaSans_600SemiBold',
  bodyBold:        'PlusJakartaSans_700Bold',
  monoMedium:      'JetBrainsMono_500Medium',
  monoBold:        'JetBrainsMono_700Bold',
} as const;
