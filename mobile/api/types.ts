/**
 * Shared API types — mirror the Pydantic schemas defined on the backend.
 *
 * These are hand-mirrored rather than auto-generated because the backend
 * uses Python-side enums that don't always survive OpenAPI → TS cleanly.
 * Keep this file in lockstep with the backend Pydantic schemas
 * (backend/app/<feature>/schemas.py).
 */

import type { AuthUser } from '../store/authSlice';

// ──────────────────────────────────────────────────────────────────────────────
// Common
// ──────────────────────────────────────────────────────────────────────────────
export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
}

export interface AuthResponse {
  user: AuthUser;
  tokens: TokenPair;
}

// ──────────────────────────────────────────────────────────────────────────────
// Reference
// ──────────────────────────────────────────────────────────────────────────────
export interface City {
  id: number;
  slug: string;
  name: string;
  country_code: string;
  timezone: string;
}

export interface Vibe {
  id: number;
  slug: string;
  name: string;
  description: string | null;
  icon_url: string | null;
}

export interface Drink {
  id: number;
  slug: string;
  name: string;
  type: string;
  description: string | null;
  image_url: string | null;
}

// The `drink_type` enum, reused to tag raids/parties for taste-matching.
export type DrinkType =
  | 'beer'
  | 'cocktail'
  | 'wine'
  | 'spirit'
  | 'non_alcoholic'
  | 'other';

export interface Race {
  id: number;
  slug: string;
  name: string;
  title: string | null;
  description: string;
  icon_url: string | null;
  primary_color: string | null;
}

export interface Interest {
  id: number;
  slug: string;
  label: string;
}

// ──────────────────────────────────────────────────────────────────────────────
// Bars
// ──────────────────────────────────────────────────────────────────────────────
export type PriceCategory = 'budget' | 'mid' | 'premium' | 'luxury';

export interface BarSummary {
  id: number;
  slug: string;
  name: string;
  city_id: number;
  address: string | null;
  image_url: string | null;
  price_category: PriceCategory;
  rating_avg: number;
  rating_count: number;
  latitude: number | null;
  longitude: number | null;
  distance_m: number | null;
  is_favorite: boolean;
}

export interface BarPhoto {
  id: number;
  url: string;
  alt_text: string | null;
  position: number;
}

export interface BarReview {
  id: number;
  user_id: number;
  rating: number;
  text: string | null;
  created_at: string;
}

export interface BarDetail extends BarSummary {
  description: string | null;
  phone: string | null;
  website: string | null;
  work_hours: Record<string, unknown>;
  photos: BarPhoto[];
  vibes: { id: number; slug: string; name: string }[];
  recent_reviews: BarReview[];
}

// ──────────────────────────────────────────────────────────────────────────────
// Friends
// ──────────────────────────────────────────────────────────────────────────────
export interface FriendUser {
  id: number;
  first_name: string;
  last_name: string | null;
  username: string;
  avatar_url: string | null;
  race_id: number | null;
}

export interface Friend {
  user: FriendUser;
  nickname: string | null;
  is_muted: boolean;
  accepted_at: string | null;
}

export interface FriendRequest {
  id: number;
  sender_id: number;
  recipient_id: number;
  message: string | null;
  status: 'pending' | 'accepted' | 'declined' | 'cancelled';
  created_at: string;
  responded_at: string | null;
}

export interface FriendGroup {
  id: number;
  owner_id: number;
  name: string;
  slug: string | null;
  description: string | null;
  image_url: string | null;
  member_count: number;
}

export interface FriendGroupMember {
  user: FriendUser;
  role: 'member' | 'admin';
  joined_at: string;
}

// ──────────────────────────────────────────────────────────────────────────────
// Quiz
// ──────────────────────────────────────────────────────────────────────────────
export interface QuizAnswer {
  id: number;
  text: string;
  position: number;
}
export interface QuizQuestion {
  id: number;
  position: number;
  text: string;
  image_url: string | null;
  answers: QuizAnswer[];
}
export interface QuizResult {
  race_id: number;
  race_slug: string;
  race_name: string;
  score_breakdown: Record<string, number>;
  completed_at: string;
}

// ──────────────────────────────────────────────────────────────────────────────
// Raids
// ──────────────────────────────────────────────────────────────────────────────
export type RaidStatus =
  | 'planned'
  | 'ongoing'
  | 'completed'
  | 'cancelled'
  | 'aborted';
// Full attendance lifecycle. Users only ever pick from RsvpChoice; the
// arrived/attended/no_show states are set by check-in + host verification.
export type RsvpStatus =
  | 'going'
  | 'maybe'
  | 'declined'
  | 'arrived'
  | 'attended'
  | 'no_show';
export type RsvpChoice = 'going' | 'maybe' | 'declined';
export type RaidVisibility = 'open' | 'friends_only';
export type AttendanceVerdict = 'attended' | 'no_show';

export interface Raid {
  id: number;
  title: string;
  description: string | null;
  bar_id: number | null;
  organizer_id: number;
  scheduled_at: string;
  ends_at: string | null;
  max_participants: number | null;
  theme: string | null;
  status: RaidStatus;
  visibility: RaidVisibility;
  cover_image_url: string | null;
  latitude: number | null;
  longitude: number | null;
  distance_m: number | null;
  participant_count: number;
  drink_types: DrinkType[];
  drink_match: number;
  my_rsvp: RsvpStatus | null;
}

export interface RaidParticipantDetail {
  user_id: number;
  username: string;
  first_name: string;
  avatar_url: string | null;
  status: RsvpStatus;
  arrived_at: string | null;
  verified_at: string | null;
}

// ──────────────────────────────────────────────────────────────────────────────
// Parties
// ──────────────────────────────────────────────────────────────────────────────
export type PartyStatus = 'open' | 'closed' | 'cancelled';
export type PartyVisibility = 'open' | 'friends_only';
export type PartyMemberStatus = 'joined' | 'left' | 'invited';

export interface Party {
  id: number;
  host_id: number;
  title: string;
  description: string | null;
  max_members: number | null;
  visibility: PartyVisibility;
  status: PartyStatus;
  interest_ids: number[];
  drink_types: DrinkType[];
  member_count: number;
  match_score: number;
  drink_match: number;
  my_membership: PartyMemberStatus | null;
  is_full: boolean;
  created_at: string;
}

export interface PartyMemberDetail {
  user_id: number;
  username: string;
  first_name: string;
  avatar_url: string | null;
  status: PartyMemberStatus;
  joined_at: string;
}

// ──────────────────────────────────────────────────────────────────────────────
// Notifications
// ──────────────────────────────────────────────────────────────────────────────
export interface NotificationRead {
  id: number;
  recipient_id: number;
  sender_id: number | null;
  type: string;
  title: string;
  body: string | null;
  data: Record<string, unknown>;
  related_entity_type: string | null;
  related_entity_id: number | null;
  read_at: string | null;
  created_at: string;
}

// ──────────────────────────────────────────────────────────────────────────────
// Checks
// ──────────────────────────────────────────────────────────────────────────────
export type ParticipantStatus = 'invited' | 'joined' | 'ready' | 'left';
export type ProposalStatus =
  | 'pending'
  | 'accepted'
  | 'declined'
  | 'completed'
  | 'cancelled';

export interface CheckItem {
  id: number;
  name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  position: number;
  assigned_quantity: number;
}

export interface CheckParticipant {
  id: number;
  user_id: number | null;
  display_name: string;
  color: string | null;
  status: ParticipantStatus;
  joined_at: string | null;
  ready_at: string | null;
  subtotal: number;
}

export interface CheckRead {
  id: number;
  user_id: number;
  bar_id: number | null;
  raid_id: number | null;
  party_id: number | null;
  bar_name_freeform: string | null;
  currency: string;
  total_amount: number;
  image_url: string | null;
  occurred_at: string | null;
  note: string | null;
  parsed_at: string | null;
  created_at: string;
  items: CheckItem[];
  participants: CheckParticipant[];
}

export interface DiceVote {
  user_id: number;
  vote: 'pending' | 'accept' | 'decline';
  voted_at: string | null;
}

export interface DiceProposal {
  id: number;
  check_id: number;
  proposed_by: number;
  status: ProposalStatus;
  decided_at: string | null;
  cancel_reason: string | null;
  created_at: string;
  votes: DiceVote[];
}

export interface KindSoulEvent {
  id: number;
  check_id: number;
  payer_user_id: number;
  total_paid_for_others: number;
  decided_via: string;
  event_metadata: Record<string, unknown>;
  occurred_at: string;
}

export interface KindSoulLeaderRow {
  user_id: number;
  first_name: string;
  username: string;
  avatar_url: string | null;
  events_count: number;
  total_paid_for_others: number;
}

// ──────────────────────────────────────────────────────────────────────────────
// Achievements
// ──────────────────────────────────────────────────────────────────────────────
export interface Achievement {
  id: number;
  code: string;
  name: string;
  description: string;
  category: string;
  race_id: number | null;
  icon_url: string | null;
  points: number;
  requirement: Record<string, unknown>;
}

export interface UserAchievement {
  achievement: Achievement;
  awarded_at: string;
  progress: Record<string, unknown>;
}

// ──────────────────────────────────────────────────────────────────────────────
// Chat
// ──────────────────────────────────────────────────────────────────────────────
export interface ChatAttachment {
  url: string;
  type: string;
  name: string | null;
  size: number | null;
}

export interface Conversation {
  id: number;
  type: 'direct' | 'group';
  title: string | null;
  image_url: string | null;
  friend_group_id: number | null;
  raid_id: number | null;
  last_message_at: string | null;
  participants: number[];
  unread_count: number;
  last_message_preview: string | null;
}

export interface ChatMessage {
  id: number;
  conversation_id: number;
  sender_id: number;
  body: string | null;
  attachments: ChatAttachment[];
  reply_to_id: number | null;
  edited_at: string | null;
  deleted_at: string | null;
  created_at: string;
  reactions: Record<string, number[]>;
}

export interface PresenceRead {
  user_id: number;
  status: 'online' | 'away' | 'offline';
  last_seen_at: string;
}

// ──────────────────────────────────────────────────────────────────────────────
// Tavern Tales
// ──────────────────────────────────────────────────────────────────────────────
export type DndMode = 'munchkin' | 'normal' | 'dungeon_master_pro';

export interface DndClassInfo {
  slug: string;
  name: string;
  description: string;
  hit_die: number;
  primary_ability: string | null;
  icon_url: string | null;
}

export interface DndCharacter {
  id: number;
  user_id: number;
  race_id: number;
  class_slug: string;
  name: string;
  level: number;
  xp: number;
  alignment: string | null;
  stats: Record<string, number>;
  hp_current: number;
  hp_max: number;
  armor_class: number;
  background: string | null;
  inventory: { slug?: string; name: string; qty?: number }[];
  spells_known: { slug?: string; name: string; level?: number }[];
  avatar_url: string | null;
  is_active: boolean;
  created_at: string;
  last_played_at: string | null;
}

export interface DndSession {
  id: number;
  character_id: number;
  mode: DndMode;
  title: string | null;
  summary: string | null;
  status: 'active' | 'paused' | 'completed' | 'abandoned';
  turn_count: number;
  input_tokens_used: number;
  output_tokens_used: number;
  session_metadata: Record<string, unknown>;
  started_at: string;
  last_message_at: string | null;
  ended_at: string | null;
}

export interface DndMessage {
  id: number;
  session_id: number;
  role: 'user' | 'assistant' | 'system' | 'dice_roll' | 'narration';
  content: string;
  message_metadata: Record<string, unknown>;
  tokens_in: number | null;
  tokens_out: number | null;
  created_at: string;
}
