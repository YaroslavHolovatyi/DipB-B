/** Raids — list, create, RSVP, cancel. */

import { api } from './index';
import type {
  AttendanceVerdict,
  DrinkType,
  Page,
  Raid,
  RaidParticipantDetail,
  RaidStatus,
  RaidVisibility,
  RsvpChoice,
} from './types';

export interface RaidListParams {
  scope?: 'mine' | 'all';
  status?: RaidStatus;
  near_lat?: number;
  near_lon?: number;
  radius_m?: number;
  limit?: number;
  offset?: number;
}

interface RaidCreateBody {
  title: string;
  description?: string | null;
  bar_id?: number | null;
  scheduled_at: string;
  ends_at?: string | null;
  max_participants?: number | null;
  theme?: string | null;
  visibility?: RaidVisibility;
  cover_image_url?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  drink_types?: DrinkType[];
  invite_user_ids?: number[];
}

interface RaidUpdateBody {
  title?: string;
  description?: string | null;
  scheduled_at?: string;
  ends_at?: string | null;
  max_participants?: number | null;
  theme?: string | null;
  visibility?: RaidVisibility;
  cover_image_url?: string | null;
  status?: RaidStatus;
  drink_types?: DrinkType[];
}

export const raidsApi = api.injectEndpoints({
  endpoints: (build) => ({
    listRaids: build.query<Page<Raid>, RaidListParams | void>({
      query: (params) => ({
        url: '/raids',
        params: (params ?? {}) as Record<string, unknown>,
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.items.map((r) => ({ type: 'Raid' as const, id: r.id })),
              { type: 'RaidList' as const, id: 'PARTIAL-LIST' },
            ]
          : [{ type: 'RaidList' as const, id: 'PARTIAL-LIST' }],
    }),
    getRaid: build.query<Raid, number>({
      query: (id) => `/raids/${id}`,
      providesTags: (_r, _e, id) => [{ type: 'Raid', id }],
    }),
    createRaid: build.mutation<Raid, RaidCreateBody>({
      query: (body) => ({ url: '/raids', method: 'POST', body }),
      invalidatesTags: [{ type: 'RaidList', id: 'PARTIAL-LIST' }],
    }),
    updateRaid: build.mutation<Raid, { id: number; body: RaidUpdateBody }>({
      query: ({ id, body }) => ({
        url: `/raids/${id}`,
        method: 'PATCH',
        body,
      }),
      invalidatesTags: (_r, _e, { id }) => [
        { type: 'Raid', id },
        { type: 'RaidList', id: 'PARTIAL-LIST' },
      ],
    }),
    cancelRaid: build.mutation<Raid, number>({
      query: (id) => ({ url: `/raids/${id}/cancel`, method: 'POST' }),
      invalidatesTags: (_r, _e, id) => [
        { type: 'Raid', id },
        { type: 'RaidList', id: 'PARTIAL-LIST' },
      ],
    }),
    rsvpRaid: build.mutation<Raid, { id: number; status: RsvpChoice }>({
      query: ({ id, status }) => ({
        url: `/raids/${id}/rsvp`,
        method: 'POST',
        body: { status },
      }),
      invalidatesTags: (_r, _e, { id }) => [
        { type: 'Raid', id },
        { type: 'RaidList', id: 'PARTIAL-LIST' },
        { type: 'RaidParticipants', id },
      ],
    }),

    // --- lifecycle ---------------------------------------------------------
    listRaidParticipants: build.query<RaidParticipantDetail[], number>({
      query: (id) => `/raids/${id}/participants`,
      providesTags: (_r, _e, id) => [{ type: 'RaidParticipants', id }],
    }),
    checkpointRaid: build.mutation<Raid, number>({
      query: (id) => ({ url: `/raids/${id}/checkpoint`, method: 'POST' }),
      invalidatesTags: (_r, _e, id) => [
        { type: 'Raid', id },
        { type: 'RaidParticipants', id },
      ],
    }),
    verifyRaid: build.mutation<
      Raid,
      { id: number; marks: { user_id: number; verdict: AttendanceVerdict }[] }
    >({
      query: ({ id, marks }) => ({
        url: `/raids/${id}/verify`,
        method: 'POST',
        body: { marks },
      }),
      invalidatesTags: (_r, _e, { id }) => [
        { type: 'Raid', id },
        { type: 'RaidParticipants', id },
      ],
    }),
    completeRaid: build.mutation<Raid, number>({
      query: (id) => ({ url: `/raids/${id}/complete`, method: 'POST' }),
      invalidatesTags: (_r, _e, id) => [
        { type: 'Raid', id },
        { type: 'RaidList', id: 'PARTIAL-LIST' },
        { type: 'RaidParticipants', id },
      ],
    }),
    abortRaid: build.mutation<Raid, number>({
      query: (id) => ({ url: `/raids/${id}/abort`, method: 'POST' }),
      invalidatesTags: (_r, _e, id) => [
        { type: 'Raid', id },
        { type: 'RaidList', id: 'PARTIAL-LIST' },
        { type: 'RaidParticipants', id },
      ],
    }),
  }),
});

export const {
  useListRaidsQuery,
  useGetRaidQuery,
  useCreateRaidMutation,
  useUpdateRaidMutation,
  useCancelRaidMutation,
  useRsvpRaidMutation,
  useListRaidParticipantsQuery,
  useCheckpointRaidMutation,
  useVerifyRaidMutation,
  useCompleteRaidMutation,
  useAbortRaidMutation,
} = raidsApi;
