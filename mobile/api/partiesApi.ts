/** Parties — discover by interest, create, join, leave, invite. */

import { api } from './index';
import type {
  DrinkType,
  Party,
  PartyMemberDetail,
  PartyStatus,
  PartyVisibility,
  Page,
} from './types';

export interface PartyListParams {
  scope?: 'mine' | 'all';
  status?: PartyStatus;
  limit?: number;
  offset?: number;
}

interface PartyCreateBody {
  title: string;
  description?: string | null;
  max_members?: number | null;
  visibility?: PartyVisibility;
  interest_ids?: number[];
  drink_types?: DrinkType[];
  invite_user_ids?: number[];
}

interface PartyUpdateBody {
  title?: string;
  description?: string | null;
  max_members?: number | null;
  visibility?: PartyVisibility;
  status?: PartyStatus;
  interest_ids?: number[];
  drink_types?: DrinkType[];
}

export const partiesApi = api.injectEndpoints({
  endpoints: (build) => ({
    listParties: build.query<Page<Party>, PartyListParams | void>({
      query: (params) => ({
        url: '/parties',
        params: (params ?? {}) as Record<string, unknown>,
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.items.map((p) => ({ type: 'Party' as const, id: p.id })),
              { type: 'PartyList' as const, id: 'PARTIAL-LIST' },
            ]
          : [{ type: 'PartyList' as const, id: 'PARTIAL-LIST' }],
    }),
    getParty: build.query<Party, number>({
      query: (id) => `/parties/${id}`,
      providesTags: (_r, _e, id) => [{ type: 'Party', id }],
    }),
    listPartyMembers: build.query<PartyMemberDetail[], number>({
      query: (id) => `/parties/${id}/members`,
      providesTags: (_r, _e, id) => [{ type: 'PartyMembers', id }],
    }),
    createParty: build.mutation<Party, PartyCreateBody>({
      query: (body) => ({ url: '/parties', method: 'POST', body }),
      invalidatesTags: [{ type: 'PartyList', id: 'PARTIAL-LIST' }],
    }),
    updateParty: build.mutation<Party, { id: number; body: PartyUpdateBody }>({
      query: ({ id, body }) => ({ url: `/parties/${id}`, method: 'PATCH', body }),
      invalidatesTags: (_r, _e, { id }) => [
        { type: 'Party', id },
        { type: 'PartyList', id: 'PARTIAL-LIST' },
      ],
    }),
    joinParty: build.mutation<Party, number>({
      query: (id) => ({ url: `/parties/${id}/join`, method: 'POST' }),
      invalidatesTags: (_r, _e, id) => [
        { type: 'Party', id },
        { type: 'PartyList', id: 'PARTIAL-LIST' },
        { type: 'PartyMembers', id },
      ],
    }),
    leaveParty: build.mutation<Party, number>({
      query: (id) => ({ url: `/parties/${id}/leave`, method: 'POST' }),
      invalidatesTags: (_r, _e, id) => [
        { type: 'Party', id },
        { type: 'PartyList', id: 'PARTIAL-LIST' },
        { type: 'PartyMembers', id },
      ],
    }),
    inviteToParty: build.mutation<Party, { id: number; user_ids: number[] }>({
      query: ({ id, user_ids }) => ({
        url: `/parties/${id}/invite`,
        method: 'POST',
        body: { user_ids },
      }),
      invalidatesTags: (_r, _e, { id }) => [
        { type: 'Party', id },
        { type: 'PartyMembers', id },
      ],
    }),
  }),
});

export const {
  useListPartiesQuery,
  useGetPartyQuery,
  useListPartyMembersQuery,
  useCreatePartyMutation,
  useUpdatePartyMutation,
  useJoinPartyMutation,
  useLeavePartyMutation,
  useInviteToPartyMutation,
} = partiesApi;
