/**
 * Static asset registry.
 *
 * React Native's Metro bundler resolves `require('./foo.png')` at build time,
 * so every asset path must be a string literal — you cannot build the path
 * dynamically. That's why these are hand-written maps keyed by the slugs the
 * backend already uses (city slug, race slug, drink_type enum).
 *
 * Helper getters return `undefined` for unknown keys so callers can fall back
 * to a vector icon or skip the image entirely.
 */
import type { ImageSourcePropType } from 'react-native';

// --------------------------------------------------------------------------- //
// Brand
// --------------------------------------------------------------------------- //
export const logo: ImageSourcePropType = require('./races/bnb-logo.png');
export const scrollBackground: ImageSourcePropType = require('./scroll-background.jpg');
export const likeIcon: ImageSourcePropType = require('./like_icon.png');

// --------------------------------------------------------------------------- //
// City icons — keyed by the DB city slug.
// A few asset filenames differ in spelling from the slug (chekasy/odessa/…);
// those are reconciled here. `kropyvnytskyi` and `simferopol` ship no art yet.
// --------------------------------------------------------------------------- //
const CITY_ICONS: Record<string, ImageSourcePropType> = {
  cherkasy: require('./city_icons/chekasy_icon.png'),
  chernihiv: require('./city_icons/chernihiv_icon.png'),
  chernivtsi: require('./city_icons/chernivtsi_icon.png'),
  dnipro: require('./city_icons/dnipro_icon.png'),
  donetsk: require('./city_icons/donetsk_icon.png'),
  'ivano-frankivsk': require('./city_icons/ivano-frankivsk_icon.png'),
  kharkiv: require('./city_icons/kharkiv_icon.png'),
  kherson: require('./city_icons/kherson_icon.png'),
  khmelnytskyi: require('./city_icons/khmelnytsk_icon.png'),
  'kryvyi-rih': require('./city_icons/kryvyi-rih_icon.png'),
  kyiv: require('./city_icons/kyiv_icon.png'),
  luhansk: require('./city_icons/luhansk_icon.png'),
  lutsk: require('./city_icons/lutsk_icon.png'),
  lviv: require('./city_icons/lviv_icon.png'),
  mariupol: require('./city_icons/mariupol_icon.png'),
  mykolaiv: require('./city_icons/mykolayiv_icon.png'),
  odesa: require('./city_icons/odessa_icon.png'),
  poltava: require('./city_icons/poltava_icon.png'),
  rivne: require('./city_icons/rivne_icon.png'),
  sevastopol: require('./city_icons/sevastopol_icon.png'),
  sumy: require('./city_icons/sumy_icon.png'),
  ternopil: require('./city_icons/ternopil_icon.png'),
  uzhhorod: require('./city_icons/uzhhorod_icon.png'),
  vinnytsia: require('./city_icons/vinnytsia_icon.png'),
  zaporizhzhia: require('./city_icons/zaporizhzhia_icon.png'),
  zhytomyr: require('./city_icons/zhytomyr_icon.png'),
};

export function cityIcon(slug?: string | null): ImageSourcePropType | undefined {
  return slug ? CITY_ICONS[slug] : undefined;
}

// --------------------------------------------------------------------------- //
// Drink-type icons — keyed by the `drink_type` enum. We only ship four pieces
// of art, so cocktails reuse the shot glass. Missing types fall back to none.
// --------------------------------------------------------------------------- //
const DRINK_ICONS: Record<string, ImageSourcePropType> = {
  beer: require('./beer_icon.png'),
  wine: require('./wine_icon.png'),
  spirit: require('./shot_icon.png'),
  cocktail: require('./shot_icon.png'),
};

export function drinkIcon(type?: string | null): ImageSourcePropType | undefined {
  return type ? DRINK_ICONS[type] : undefined;
}

// --------------------------------------------------------------------------- //
// Race avatars — keyed by race slug, then gender. Every race has male + female
// art. The DB race `orc` is illustrated by the half-orc piece. Unknown gender
// falls back to the male art (see `raceImage`).
// --------------------------------------------------------------------------- //
type GenderedArt = { m: ImageSourcePropType; f: ImageSourcePropType };

const RACE_IMAGES: Record<string, GenderedArt> = {
  human: { m: require('./races/human_m.jpg'), f: require('./races/human_f.jpg') },
  elf: { m: require('./races/elf_m.jpg'), f: require('./races/elf_f.jpg') },
  dwarf: { m: require('./races/dwarf_m.jpg'), f: require('./races/dwarf_f.jpg') },
  halfling: { m: require('./races/halfing_m.jpg'), f: require('./races/halfing_f.jpg') },
  orc: { m: require('./races/half-orc_m.jpg'), f: require('./races/half-orc_f.jpg') },
  gnome: { m: require('./races/gnome_m.jpg'), f: require('./races/gnome_f.jpg') },
  tiefling: { m: require('./races/tiefling_m.jpg'), f: require('./races/tiefling_f.jpg') },
  dragonborn: { m: require('./races/dragonborn_m.jpg'), f: require('./races/dragonborn_f.jpg') },
};

export function raceImage(
  slug?: string | null,
  gender?: string | null,
): ImageSourcePropType | undefined {
  const art = slug ? RACE_IMAGES[slug] : undefined;
  if (!art) return undefined;
  return gender === 'f' ? art.f : art.m;
}
