/** Display labels for the `drink_type` enum, used by the event-tag chips. */

import type { ComponentProps } from 'react';
import type { Ionicons } from '@expo/vector-icons';

import type { DrinkType } from '../api/types';

type IoniconName = ComponentProps<typeof Ionicons>['name'];

export const DRINK_TYPE_OPTIONS: {
  value: DrinkType;
  label: string;
  icon: IoniconName;
}[] = [
  { value: 'beer', label: 'Beer', icon: 'beer' },
  { value: 'cocktail', label: 'Cocktails', icon: 'wine' },
  { value: 'wine', label: 'Wine', icon: 'wine' },
  { value: 'spirit', label: 'Spirits', icon: 'flask' },
  { value: 'non_alcoholic', label: 'Non-alcoholic', icon: 'cafe' },
  { value: 'other', label: 'Other', icon: 'pint' },
];

const LABELS: Record<DrinkType, string> = Object.fromEntries(
  DRINK_TYPE_OPTIONS.map((o) => [o.value, o.label]),
) as Record<DrinkType, string>;

const ICONS: Record<DrinkType, IoniconName> = Object.fromEntries(
  DRINK_TYPE_OPTIONS.map((o) => [o.value, o.icon]),
) as Record<DrinkType, IoniconName>;

export const drinkLabel = (t: DrinkType): string => LABELS[t] ?? t;
export const drinkIonicon = (t: DrinkType): IoniconName => ICONS[t] ?? 'pint';
