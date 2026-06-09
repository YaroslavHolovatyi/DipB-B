/**
 * Shared types for the Home Feed screen.
 * These will eventually be replaced by RTK Query response types once the API is wired up.
 */

export type FantasyRace = 'human' | 'elf' | 'dwarf' | 'orc' | 'halfling' | 'gnome';

export type RsvpStatus = 'going' | 'maybe' | 'declined' | 'pending';

export interface Tavern {
  id: string;
  name: string;
  vibe: string;        // e.g. "🍺 Craft", "🎸 Live", "🕯 Cozy"
  distanceKm: number;
  rating: number;      // 1–5
  gradientColors: [string, string];  // for the image placeholder gradient
}

export interface Raid {
  id: string;
  name: string;
  tavernName: string;
  partySize: number;
  time: string;        // "19:00"
  date: string;        // "Fri, May 29"
  rsvp: RsvpStatus;
  icon: string;        // emoji
}

export interface ActivityEvent {
  id: string;
  actorName: string;
  actorInitial: string;
  actorRace: FantasyRace;
  text: string;        // rich text with **bold** spans handled manually
  boldParts: string[]; // which substrings to render bold
  timeAgo: string;     // "2m", "14m", "1h"
}
