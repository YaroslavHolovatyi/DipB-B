import type { FantasyRace } from './home';

export type AchievementState = 'unlocked' | 'rare' | 'locked';

export interface Achievement {
  id: string;
  emoji: string;
  name: string;
  state: AchievementState;
}

export interface LeaderboardEntry {
  rank: number;
  initial: string;
  name: string;
  race: FantasyRace;
  city: string;
  score: number;
  isCurrentUser?: boolean;
}

export interface FavouriteTavern {
  id: string;
  name: string;
  emoji: string;
  gradientColors: [string, string];
}

export interface UserProfile {
  displayName: string;
  username: string;
  city: string;
  race: FantasyRace;
  raceEmoji: string;
  raceLabel: string;
  level: number;
  xpCurrent: number;
  xpNext: number;
  stats: {
    checkIns: number;
    raids: number;
    friends: number;
    kindSoul: number;
  };
}
