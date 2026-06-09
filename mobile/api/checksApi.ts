/**
 * Checks (receipts) — upload, split-room flow, dice game.
 *
 * Returns the full `CheckRead` shape after every state transition so the UI
 * always has fresh totals. WebSocket events `assignment.updated` /
 * `participant.joined` / etc. invalidate the relevant Check tag.
 */

import { api } from './index';
import type {
  CheckRead,
  DiceProposal,
  KindSoulEvent,
  KindSoulLeaderRow,
} from './types';

interface CheckCreateBody {
  image_url: string;
  bar_id?: number | null;
  occurred_at?: string | null;
  note?: string | null;
}

interface EventCheckCreateBody {
  image_url: string;
  raid_id?: number | null;
  party_id?: number | null;
  occurred_at?: string | null;
  note?: string | null;
}

interface ReceiptUploadResponse {
  upload_url: string;
  public_url: string;
  key: string;
  expires_in: number;
}

interface InviteBody {
  user_ids?: number[];
  guests?: string[];
}

interface AssignmentBody {
  participant_id: number;
  quantity: number;
}

export const checksApi = api.injectEndpoints({
  endpoints: (build) => ({
    listChecks: build.query<CheckRead[], { limit?: number; offset?: number } | void>({
      query: (params) => ({
        url: '/checks',
        params: (params ?? {}) as Record<string, unknown>,
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.map((c) => ({ type: 'Check' as const, id: c.id })),
              { type: 'CheckList' as const, id: 'PARTIAL-LIST' },
            ]
          : [{ type: 'CheckList' as const, id: 'PARTIAL-LIST' }],
    }),
    getCheck: build.query<CheckRead, number>({
      query: (id) => `/checks/${id}`,
      providesTags: (_r, _e, id) => [{ type: 'Check', id }],
    }),
    createCheck: build.mutation<CheckRead, CheckCreateBody>({
      query: (body) => ({ url: '/checks', method: 'POST', body }),
      invalidatesTags: [{ type: 'CheckList', id: 'PARTIAL-LIST' }],
    }),
    createEventCheck: build.mutation<CheckRead, EventCheckCreateBody>({
      query: (body) => ({ url: '/checks/from-event', method: 'POST', body }),
      invalidatesTags: [{ type: 'CheckList', id: 'PARTIAL-LIST' }],
    }),
    receiptUploadUrl: build.mutation<ReceiptUploadResponse, { content_type?: string }>({
      query: (body) => ({ url: '/checks/upload-url', method: 'POST', body }),
    }),
    invite: build.mutation<CheckRead, { id: number; body: InviteBody }>({
      query: ({ id, body }) => ({
        url: `/checks/${id}/invite`,
        method: 'POST',
        body,
      }),
      invalidatesTags: (_r, _e, { id }) => [{ type: 'Check', id }],
    }),
    join: build.mutation<CheckRead, number>({
      query: (id) => ({ url: `/checks/${id}/join`, method: 'POST' }),
      invalidatesTags: (_r, _e, id) => [{ type: 'Check', id }],
    }),
    leave: build.mutation<CheckRead, number>({
      query: (id) => ({ url: `/checks/${id}/leave`, method: 'POST' }),
      invalidatesTags: (_r, _e, id) => [{ type: 'Check', id }],
    }),
    setReady: build.mutation<CheckRead, { id: number; ready: boolean }>({
      query: ({ id, ready }) => ({
        url: `/checks/${id}/${ready ? 'ready' : 'unready'}`,
        method: 'POST',
      }),
      invalidatesTags: (_r, _e, { id }) => [{ type: 'Check', id }],
    }),
    upsertAssignment: build.mutation<
      CheckRead,
      { check_id: number; item_id: number; body: AssignmentBody }
    >({
      query: ({ check_id, item_id, body }) => ({
        url: `/checks/${check_id}/items/${item_id}/assignments`,
        method: 'PUT',
        body,
      }),
      invalidatesTags: (_r, _e, { check_id }) => [
        { type: 'Check', id: check_id },
      ],
    }),
    removeAssignment: build.mutation<
      CheckRead,
      { check_id: number; item_id: number; participant_id: number }
    >({
      query: ({ check_id, item_id, participant_id }) => ({
        url: `/checks/${check_id}/items/${item_id}/assignments/${participant_id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_r, _e, { check_id }) => [
        { type: 'Check', id: check_id },
      ],
    }),

    // Dice
    proposeDice: build.mutation<DiceProposal, number>({
      query: (id) => ({ url: `/checks/${id}/dice/propose`, method: 'POST' }),
      invalidatesTags: (_r, _e, id) => [{ type: 'Check', id }],
    }),
    voteDice: build.mutation<
      DiceProposal | KindSoulEvent,
      { check_id: number; proposal_id: number; vote: 'accept' | 'decline' }
    >({
      query: ({ check_id, proposal_id, vote }) => ({
        url: `/checks/${check_id}/dice/${proposal_id}/vote`,
        method: 'POST',
        body: { vote },
      }),
      invalidatesTags: (_r, _e, { check_id }) => [
        { type: 'Check', id: check_id },
        'Leaderboard',
      ],
    }),
    kindSoulLeaderboard: build.query<KindSoulLeaderRow[], number | void>({
      query: (limit) => ({
        url: '/checks/_/kind-soul/leaderboard',
        params: limit ? { limit } : undefined,
      }),
      providesTags: ['Leaderboard'],
    }),
  }),
});

export const {
  useListChecksQuery,
  useGetCheckQuery,
  useCreateCheckMutation,
  useCreateEventCheckMutation,
  useReceiptUploadUrlMutation,
  useInviteMutation,
  useJoinMutation,
  useLeaveMutation,
  useSetReadyMutation,
  useUpsertAssignmentMutation,
  useRemoveAssignmentMutation,
  useProposeDiceMutation,
  useVoteDiceMutation,
  useKindSoulLeaderboardQuery,
} = checksApi;
