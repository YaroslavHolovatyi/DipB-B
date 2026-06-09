/**
 * Users — profile self-service, avatar upload, push tokens.
 *
 * The "me" query lives in authApi (so it can be invalidated by the auth
 * mutations); this file only adds profile-edit + push-token endpoints.
 */

import { api } from './index';
import type { Interest } from './types';
import type { AuthUser } from '../store/authSlice';

interface UserUpdate {
  first_name?: string;
  last_name?: string | null;
  avatar_url?: string | null;
  main_city_id?: number;
  bio?: string | null;
}

export interface UserStats {
  social_rating: number;
  events_attended: number;
  events_ditched: number;
  events_total: number;
  reliability_pct: number | null;
  rating_tier: string;
}

interface AvatarPresignBody {
  content_type?: string;
}

interface AvatarPresignResponse {
  upload_url: string;
  public_url: string;
  key: string;
  expires_in: number;
}

interface PushTokenRegister {
  token: string;
  platform: 'ios' | 'android' | 'web';
}

interface PushTokenRead {
  id: number;
  token: string;
  platform: string;
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
}

export const usersApi = api.injectEndpoints({
  endpoints: (build) => ({
    updateMe: build.mutation<AuthUser, UserUpdate>({
      query: (body) => ({ url: '/users/me', method: 'PATCH', body }),
      invalidatesTags: ['User'],
    }),
    myStats: build.query<UserStats, void>({
      query: () => '/users/me/stats',
      providesTags: ['UserStats'],
    }),
    myInterests: build.query<Interest[], void>({
      query: () => '/users/me/interests',
      providesTags: ['MyInterests'],
    }),
    setMyInterests: build.mutation<Interest[], number[]>({
      query: (interest_ids) => ({
        url: '/users/me/interests',
        method: 'PUT',
        body: { interest_ids },
      }),
      invalidatesTags: ['MyInterests'],
    }),
    presignAvatar: build.mutation<AvatarPresignResponse, AvatarPresignBody>({
      query: (body) => ({
        url: '/users/me/avatar-upload',
        method: 'POST',
        body,
      }),
    }),
    listPushTokens: build.query<PushTokenRead[], void>({
      query: () => '/users/me/push-tokens',
      providesTags: ['PushTokens'],
    }),
    registerPushToken: build.mutation<PushTokenRead, PushTokenRegister>({
      query: (body) => ({
        url: '/users/me/push-tokens',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['PushTokens'],
    }),
    revokePushToken: build.mutation<void, number>({
      query: (id) => ({
        url: `/users/me/push-tokens/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['PushTokens'],
    }),
  }),
});

export const {
  useUpdateMeMutation,
  useMyStatsQuery,
  useMyInterestsQuery,
  useSetMyInterestsMutation,
  usePresignAvatarMutation,
  useListPushTokensQuery,
  useRegisterPushTokenMutation,
  useRevokePushTokenMutation,
} = usersApi;
