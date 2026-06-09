/** Display labels for the `drink_type` enum, used by the event-tag chips. */

import type { DrinkType } from '../api/types';

export const DRINK_TYPE_OPTIONS: { value: DrinkType; label: string }[] = [
  { value: 'beer', label: '🍺 Beer' },
  { value: 'cocktail', label: '🍸 Cocktails' },
  { value: 'wine', label: '🍷 Wine' },
  { value: 'spirit', label: '🥃 Spirits' },
  { value: 'non_alcoholic', label: '🧃 Non-alcoholic' },
  { value: 'other', label: '🍹 Other' },
];

const LABELS: Record<DrinkType, string> = Object.fromEntries(
  DRINK_TYPE_OPTIONS.map((o) => [o.value, o.label]),
) as Record<DrinkType, string>;

export const drinkLabel = (t: DrinkType): string => LABELS[t] ?? t;
