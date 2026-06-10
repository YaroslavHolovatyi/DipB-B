/** Tavern Tales (D&D AI DM). */

import { api } from './index';
import type {
  DndCharacter,
  DndClassInfo,
  DndMessage,
  DndSession,
} from './types';

interface CharacterCreate {
  name: string;
  class_slug: string;
  alignment?: string | null;
  stats?: Record<string, number>;
  background?: string | null;
  avatar_url?: string | null;
}

interface SessionCreate {
  character_id: number;
  mode: 'munchkin' | 'normal' | 'dungeon_master_pro';
  title?: string | null;
}

interface TurnResponse {
  user_message: DndMessage;
  assistant_message: DndMessage;
  session: DndSession;
}

interface DiceRollBody {
  dice?: string;
  modifier?: number;
  result: number;
  purpose?: string | null;
}

interface Quota {
  user_id: number;
  daily_tokens_used: number;
  daily_tokens_limit: number;
  daily_reset_at: string;
  monthly_tokens_used: number;
  monthly_tokens_limit: number;
  monthly_reset_at: string;
}

export const tavernApi = api.injectEndpoints({
  endpoints: (build) => ({
    listClasses: build.query<DndClassInfo[], void>({
      query: () => '/tavern/classes',
      providesTags: ['DndClassInfo'],
    }),

    // Characters
    listCharacters: build.query<DndCharacter[], void>({
      query: () => '/tavern/characters',
      providesTags: ['DndCharacter'],
    }),
    createCharacter: build.mutation<DndCharacter, CharacterCreate>({
      query: (body) => ({ url: '/tavern/characters', method: 'POST', body }),
      invalidatesTags: ['DndCharacter'],
    }),
    getCharacter: build.query<DndCharacter, number>({
      query: (id) => `/tavern/characters/${id}`,
      providesTags: (_r, _e, id) => [{ type: 'DndCharacter', id }],
    }),
    updateCharacter: build.mutation<
      DndCharacter,
      { id: number; body: Partial<CharacterCreate> }
    >({
      query: ({ id, body }) => ({
        url: `/tavern/characters/${id}`,
        method: 'PATCH',
        body,
      }),
      invalidatesTags: (_r, _e, { id }) => [{ type: 'DndCharacter', id }],
    }),
    deleteCharacter: build.mutation<void, number>({
      query: (id) => ({ url: `/tavern/characters/${id}`, method: 'DELETE' }),
      invalidatesTags: ['DndCharacter'],
    }),

    // Sessions
    createSession: build.mutation<DndSession, SessionCreate>({
      query: (body) => ({ url: '/tavern/sessions', method: 'POST', body }),
      invalidatesTags: ['DndSession'],
    }),
    listSessions: build.query<DndSession[], number>({
      query: (character_id) =>
        `/tavern/characters/${character_id}/sessions`,
      providesTags: (_r, _e, id) => [{ type: 'DndSession', id }],
    }),
    listSessionMessages: build.query<DndMessage[], number>({
      query: (session_id) => `/tavern/sessions/${session_id}/messages`,
      providesTags: (_r, _e, id) => [{ type: 'DndMessage', id }],
    }),
    takeTurn: build.mutation<
      TurnResponse,
      { session_id: number; content: string }
    >({
      query: ({ session_id, content }) => ({
        url: `/tavern/sessions/${session_id}/turn`,
        method: 'POST',
        body: { content },
      }),
      invalidatesTags: (_r, _e, { session_id }) => [
        { type: 'DndMessage', id: session_id },
        'DndQuota',
      ],
    }),
    rollDice: build.mutation<
      DndMessage,
      { session_id: number; body: DiceRollBody }
    >({
      query: ({ session_id, body }) => ({
        url: `/tavern/sessions/${session_id}/roll`,
        method: 'POST',
        body,
      }),
      invalidatesTags: (_r, _e, { session_id }) => [
        { type: 'DndMessage', id: session_id },
      ],
    }),
    endSession: build.mutation<
      DndSession,
      { session_id: number; status?: string }
    >({
      query: ({ session_id, status }) => ({
        url: `/tavern/sessions/${session_id}/end`,
        method: 'POST',
        params: status ? { status } : undefined,
      }),
      invalidatesTags: ['DndSession'],
    }),
    quota: build.query<Quota, void>({
      query: () => '/tavern/quota',
      providesTags: ['DndQuota'],
    }),
  }),
});

export const {
  useListClassesQuery,
  useListCharactersQuery,
  useCreateCharacterMutation,
  useGetCharacterQuery,
  useUpdateCharacterMutation,
  useDeleteCharacterMutation,
  useCreateSessionMutation,
  useListSessionsQuery,
  useLazyListSessionsQuery,
  useListSessionMessagesQuery,
  useTakeTurnMutation,
  useRollDiceMutation,
  useEndSessionMutation,
  useQuotaQuery,
} = tavernApi;
