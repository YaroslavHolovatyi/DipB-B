/**
 * Static mock data for the Home Feed.
 * Replace each array with RTK Query hooks once the backend endpoints are ready.
 */
import type { Tavern, Raid, ActivityEvent } from '../types/home';

export const MOCK_TAVERNS: Tavern[] = [
  {
    id: '1',
    name: 'Lviv Craft Haven',
    vibe: '🍺 Craft',
    distanceKm: 0.4,
    rating: 4.8,
    gradientColors: ['#7C3F00', '#B8761A'],
  },
  {
    id: '2',
    name: "The Dragon's Den",
    vibe: '🎸 Live',
    distanceKm: 1.1,
    rating: 4.6,
    gradientColors: ['#1A3A5C', '#2D6A8A'],
  },
  {
    id: '3',
    name: 'Old Quarter Pub',
    vibe: '🕯 Cozy',
    distanceKm: 1.8,
    rating: 4.5,
    gradientColors: ['#2D3748', '#4A5568'],
  },
  {
    id: '4',
    name: 'Arcane Alehouse',
    vibe: '✨ Magic',
    distanceKm: 2.2,
    rating: 4.7,
    gradientColors: ['#4A1942', '#7B2F6E'],
  },
  {
    id: '5',
    name: 'The Iron Flagon',
    vibe: '⚒️ Rustic',
    distanceKm: 2.9,
    rating: 4.4,
    gradientColors: ['#3B2A1A', '#6B4A2A'],
  },
];

export const MOCK_RAIDS: Raid[] = [
  {
    id: 'r1',
    name: 'Friday Night Fellowship',
    tavernName: 'Lviv Craft Haven',
    partySize: 5,
    time: '19:00',
    date: 'Fri, May 29',
    rsvp: 'going',
    icon: '🍻',
  },
  {
    id: 'r2',
    name: 'Weekend Warriors',
    tavernName: "The Dragon's Den",
    partySize: 3,
    time: '21:30',
    date: 'Sat, May 30',
    rsvp: 'maybe',
    icon: '⚔️',
  },
];

export const MOCK_ACTIVITY: ActivityEvent[] = [
  {
    id: 'a1',
    actorName: 'Sophia (Elf)',
    actorInitial: 'S',
    actorRace: 'elf',
    text: 'Sophia (Elf) checked in at Arcane Alehouse ✨',
    boldParts: ['Sophia (Elf)', 'Arcane Alehouse'],
    timeAgo: '2m',
  },
  {
    id: 'a2',
    actorName: 'Max (Orc)',
    actorInitial: 'M',
    actorRace: 'orc',
    text: "Max (Orc) became the 🏆 Kind Soul at The Dragon's Den",
    boldParts: ['Max (Orc)', "The Dragon's Den"],
    timeAgo: '14m',
  },
  {
    id: 'a3',
    actorName: 'Andriy (Human)',
    actorInitial: 'A',
    actorRace: 'human',
    text: 'Andriy (Human) created a Raid — Friday Night Fellowship',
    boldParts: ['Andriy (Human)', 'Friday Night Fellowship'],
    timeAgo: '1h',
  },
  {
    id: 'a4',
    actorName: 'Kateryna (Dwarf)',
    actorInitial: 'K',
    actorRace: 'dwarf',
    text: 'Kateryna (Dwarf) unlocked achievement: 🍺 Century Drinker',
    boldParts: ['Kateryna (Dwarf)', '🍺 Century Drinker'],
    timeAgo: '3h',
  },
];
