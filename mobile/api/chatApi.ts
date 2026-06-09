/** Chat — conversations, messages, reactions, read receipts, presence. */

import { api } from './index';
import type {
  ChatAttachment,
  ChatMessage,
  Conversation,
  PresenceRead,
} from './types';

interface CreateConversationBody {
  type: 'direct' | 'group';
  participant_ids: number[];
  title?: string | null;
  friend_group_id?: number | null;
}

interface MessageCreate {
  body?: string | null;
  attachments?: ChatAttachment[];
  reply_to_id?: number | null;
}

export const chatApi = api.injectEndpoints({
  endpoints: (build) => ({
    listConversations: build.query<Conversation[], void>({
      query: () => '/chat/conversations',
      providesTags: ['Conversation'],
    }),
    createConversation: build.mutation<Conversation, CreateConversationBody>({
      query: (body) => ({
        url: '/chat/conversations',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Conversation'],
    }),
    getConversation: build.query<Conversation, number>({
      query: (id) => `/chat/conversations/${id}`,
      providesTags: (_r, _e, id) => [{ type: 'Conversation', id }],
    }),
    listMessages: build.query<
      ChatMessage[],
      { conversation_id: number; before_id?: number; limit?: number }
    >({
      query: ({ conversation_id, ...params }) => ({
        url: `/chat/conversations/${conversation_id}/messages`,
        params: params as Record<string, unknown>,
      }),
      providesTags: (_r, _e, { conversation_id }) => [
        { type: 'Message', id: conversation_id },
      ],
      // Keep the cache stable when paginating older messages.
      serializeQueryArgs: ({ queryArgs }) => `conv-${queryArgs.conversation_id}`,
      merge: (current, incoming) => {
        const seen = new Set(current.map((m) => m.id));
        const fresh = incoming.filter((m) => !seen.has(m.id));
        return [...fresh, ...current].sort(
          (a, b) => a.created_at.localeCompare(b.created_at),
        );
      },
      forceRefetch: ({ currentArg, previousArg }) =>
        currentArg?.before_id !== previousArg?.before_id,
    }),
    sendMessage: build.mutation<
      ChatMessage,
      { conversation_id: number; body: MessageCreate }
    >({
      query: ({ conversation_id, body }) => ({
        url: `/chat/conversations/${conversation_id}/messages`,
        method: 'POST',
        body,
      }),
      // Live cache update is driven by the WS `message.new` event, but we still
      // invalidate the conversation list so the preview text + unread counter
      // re-fetch.
      invalidatesTags: ['Conversation'],
    }),
    editMessage: build.mutation<
      ChatMessage,
      { message_id: number; body: string }
    >({
      query: ({ message_id, body }) => ({
        url: `/chat/messages/${message_id}`,
        method: 'PATCH',
        body: { body },
      }),
    }),
    deleteMessage: build.mutation<void, number>({
      query: (message_id) => ({
        url: `/chat/messages/${message_id}`,
        method: 'DELETE',
      }),
    }),
    toggleReaction: build.mutation<
      void,
      { message_id: number; emoji: string }
    >({
      query: ({ message_id, emoji }) => ({
        url: `/chat/messages/${message_id}/reactions`,
        method: 'POST',
        body: { emoji },
      }),
    }),
    markConversationRead: build.mutation<
      void,
      { conversation_id: number; up_to_message_id: number }
    >({
      query: ({ conversation_id, up_to_message_id }) => ({
        url: `/chat/conversations/${conversation_id}/read`,
        method: 'POST',
        body: { up_to_message_id },
      }),
      invalidatesTags: ['Conversation'],
    }),
    listPresence: build.query<PresenceRead[], number[]>({
      query: (user_ids) => ({
        url: '/chat/presence',
        params: { user_ids },
      }),
      providesTags: ['Presence'],
    }),
  }),
});

export const {
  useListConversationsQuery,
  useCreateConversationMutation,
  useGetConversationQuery,
  useListMessagesQuery,
  useSendMessageMutation,
  useEditMessageMutation,
  useDeleteMessageMutation,
  useToggleReactionMutation,
  useMarkConversationReadMutation,
  useListPresenceQuery,
} = chatApi;
