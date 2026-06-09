import type { UserProfile, Achievement, LeaderboardEntry, FavouriteTavern } from '../types/profile';

export const MOCK_USER: UserProfile = {
  displayName: 'Yaroslav',
  username:    'yaroslav_dwarf',
  city:        'Lviv',
  race:        'dwarf',
  raceEmoji:   '⚒️',
  raceLabel:   'Dwarf',
  level:       12,
  xpCurrent:   2340,
  xpNext:      3500,
  stats: {
    checkIns: 47,
    raids:    12,
    friends:  28,
    kindSoul:  3,
  },
};

export const MOCK_ACHIEVEMENTS: Achievement[] = [
  { id: 'a1', emoji: '🍺', name: 'First Flagon',  state: 'unlocked' },
  { id: 'a2', emoji: '⚔️', name: 'First Raid',    state: 'unlocked' },
  { id: 'a3', emoji: '🎲', name: 'Lucky Dice',    state: 'rare'     },
  { id: 'a4', emoji: '🗺️', name: 'Explorer',      state: 'unlocked' },
  { id: 'a5', emoji: '💰', name: 'Kind Soul',     state: 'unlocked' },
  { id: 'a6', emoji: '🏔️', name: 'Peak Raider',   state: 'locked'   },
  { id: 'a7', emoji: '⭐', name: 'Century Club',  state: 'locked'   },
  { id: 'a8', emoji: '👑', name: 'Tavern King',   state: 'locked'   },
];

export const MOCK_LEADERBOARD: LeaderboardEntry[] = [
  { rank: 1, initial: 'M', name: 'Max',              race: 'orc',   city: 'Lviv', score: 3850 },
  { rank: 2, initial: 'S', name: 'Sophia',           race: 'elf',   city: 'Lviv', score: 3210 },
  { rank: 5, initial: 'Y', name: 'You (Yaroslav)',   race: 'dwarf', city: 'Lviv', score: 2340, isCurrentUser: true },
];

export const MOCK_FAVOURITES: FavouriteTavern[] = [
  { id: 'f1', name: 'Lviv Craft Haven',  emoji: '🍺', gradientColors: ['#7C3F00', '#B8761A'] },
  { id: 'f2', name: "The Dragon's Den",  emoji: '🐉', gradientColors: ['#1A3A5C', '#2D6A8A'] },
  { id: 'f3', name: 'Arcane Alehouse',   emoji: '✨', gradientColors: ['#4A1942', '#7B2F6E'] },
  { id: 'f4', name: 'Elven Grove Bar',   emoji: '🌿', gradientColors: ['#1C3A1C', '#2D5E2D'] },
];
