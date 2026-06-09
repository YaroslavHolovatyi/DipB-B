/**
 * Single RTK Query API instance.
 *
 * RTK Query encourages putting every endpoint on one `createApi` so cache
 * invalidation across domains "just works" (e.g. accepting a friend request
 * invalidates both the friends list and the requests list). We declare the
 * tag types here and use injection (`injectEndpoints`) in each domain file.
 */

import { createApi } from '@reduxjs/toolkit/query/react';

import { baseQueryWithRefresh } from './baseQuery';

export const api = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithRefresh,
  tagTypes: [
    'Auth',
    'Cities',
    'Vibes',
    'Drinks',
    'Races',
    'Interests',
    'User',
    'UserStats',
    'MyInterests',
    'PushTokens',
    'Bar',
    'BarList',
    'BarFavorites',
    'BarReview',
    'Quiz',
    'QuizResult',
    'Friend',
    'FriendRequest',
    'FriendGroup',
    'FriendGroupMembers',
    'Raid',
    'RaidList',
    'RaidParticipants',
    'Party',
    'PartyList',
    'PartyMembers',
    'Notification',
    'Check',
    'CheckList',
    'Leaderboard',
    'Achievement',
    'UserAchievement',
    'Conversation',
    'Message',
    'Presence',
    'DndClassInfo',
    'DndCharacter',
    'DndSession',
    'DndMessage',
    'DndQuota',
  ] as const,
  endpoints: () => ({}),
});
