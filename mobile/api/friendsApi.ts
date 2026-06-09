/** Friends + friend groups. */

import { api } from './index';
import type {
  Friend,
  FriendGroup,
  FriendGroupMember,
  FriendRequest,
} from './types';

interface SendRequestBody {
  recipient_id: number;
  message?: string | null;
}

interface CreateGroupBody {
  name: string;
  description?: string | null;
  image_url?: string | null;
  initial_member_ids?: number[];
}

export const friendsApi = api.injectEndpoints({
  endpoints: (build) => ({
    listFriends: build.query<Friend[], void>({
      query: () => '/friends',
      providesTags: ['Friend'],
    }),
    listIncomingRequests: build.query<FriendRequest[], void>({
      query: () => '/friends/requests/incoming',
      providesTags: ['FriendRequest'],
    }),
    listOutgoingRequests: build.query<FriendRequest[], void>({
      query: () => '/friends/requests/outgoing',
      providesTags: ['FriendRequest'],
    }),
    sendFriendRequest: build.mutation<FriendRequest, SendRequestBody>({
      query: (body) => ({ url: '/friends/requests', method: 'POST', body }),
      invalidatesTags: ['FriendRequest'],
    }),
    acceptFriendRequest: build.mutation<FriendRequest, number>({
      query: (id) => ({
        url: `/friends/requests/${id}/accept`,
        method: 'POST',
      }),
      invalidatesTags: ['FriendRequest', 'Friend'],
    }),
    declineFriendRequest: build.mutation<FriendRequest, number>({
      query: (id) => ({
        url: `/friends/requests/${id}/decline`,
        method: 'POST',
      }),
      invalidatesTags: ['FriendRequest'],
    }),
    cancelFriendRequest: build.mutation<FriendRequest, number>({
      query: (id) => ({
        url: `/friends/requests/${id}/cancel`,
        method: 'POST',
      }),
      invalidatesTags: ['FriendRequest'],
    }),

    // Friend groups
    listFriendGroups: build.query<FriendGroup[], void>({
      query: () => '/friend-groups',
      providesTags: ['FriendGroup'],
    }),
    createFriendGroup: build.mutation<FriendGroup, CreateGroupBody>({
      query: (body) => ({ url: '/friend-groups', method: 'POST', body }),
      invalidatesTags: ['FriendGroup'],
    }),
    listFriendGroupMembers: build.query<FriendGroupMember[], number>({
      query: (id) => `/friend-groups/${id}/members`,
      providesTags: (_r, _e, id) => [{ type: 'FriendGroupMembers', id }],
    }),
    addFriendGroupMember: build.mutation<
      void,
      { group_id: number; user_id: number }
    >({
      query: ({ group_id, user_id }) => ({
        url: `/friend-groups/${group_id}/members/${user_id}`,
        method: 'POST',
      }),
      invalidatesTags: (_r, _e, { group_id }) => [
        { type: 'FriendGroupMembers', id: group_id },
      ],
    }),
    removeFriendGroupMember: build.mutation<
      void,
      { group_id: number; user_id: number }
    >({
      query: ({ group_id, user_id }) => ({
        url: `/friend-groups/${group_id}/members/${user_id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_r, _e, { group_id }) => [
        { type: 'FriendGroupMembers', id: group_id },
      ],
    }),
  }),
});

export const {
  useListFriendsQuery,
  useListIncomingRequestsQuery,
  useListOutgoingRequestsQuery,
  useSendFriendRequestMutation,
  useAcceptFriendRequestMutation,
  useDeclineFriendRequestMutation,
  useCancelFriendRequestMutation,
  useListFriendGroupsQuery,
  useCreateFriendGroupMutation,
  useListFriendGroupMembersQuery,
  useAddFriendGroupMemberMutation,
  useRemoveFriendGroupMemberMutation,
} = friendsApi;
