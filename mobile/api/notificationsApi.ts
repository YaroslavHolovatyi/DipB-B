/** Notifications. */

import { api } from './index';
import type { NotificationRead, Page } from './types';

interface ListParams {
  unread_only?: boolean;
  limit?: number;
  offset?: number;
}

export const notificationsApi = api.injectEndpoints({
  endpoints: (build) => ({
    listNotifications: build.query<Page<NotificationRead>, ListParams | void>({
      query: (params) => ({
        url: '/notifications',
        params: (params ?? {}) as Record<string, unknown>,
      }),
      providesTags: ['Notification'],
    }),
    unreadCount: build.query<{ unread: number }, void>({
      query: () => '/notifications/unread-count',
      providesTags: ['Notification'],
    }),
    markRead: build.mutation<void, number>({
      query: (id) => ({
        url: `/notifications/${id}/read`,
        method: 'POST',
      }),
      invalidatesTags: ['Notification'],
    }),
    markAllRead: build.mutation<void, void>({
      query: () => ({ url: '/notifications/read-all', method: 'POST' }),
      invalidatesTags: ['Notification'],
    }),
  }),
});

export const {
  useListNotificationsQuery,
  useUnreadCountQuery,
  useMarkReadMutation,
  useMarkAllReadMutation,
} = notificationsApi;
