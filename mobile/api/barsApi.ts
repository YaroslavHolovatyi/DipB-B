/**
 * Bars — catalog + search + favorites + reviews.
 *
 * The catalog query covers everything from "near me" to vibe filters. The
 * list cache key includes the filter object so different filter screens
 * cache independently.
 */

import { api } from './index';
import type {
  BarDetail,
  BarReview,
  BarSummary,
  Page,
  PriceCategory,
} from './types';

export interface BarListParams {
  q?: string;
  city_id?: number;
  price_category?: PriceCategory;
  vibe_id?: number;
  min_rating?: number;
  near_lat?: number;
  near_lon?: number;
  radius_m?: number;
  limit?: number;
  offset?: number;
}

interface BarReviewCreate {
  bar_id: number;
  rating: number;
  text?: string | null;
}

export const barsApi = api.injectEndpoints({
  endpoints: (build) => ({
    listBars: build.query<Page<BarSummary>, BarListParams | void>({
      query: (params) => ({
        url: '/bars',
        params: (params ?? {}) as Record<string, unknown>,
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.items.map((b) => ({ type: 'Bar' as const, id: b.id })),
              { type: 'BarList' as const, id: 'PARTIAL-LIST' },
            ]
          : [{ type: 'BarList' as const, id: 'PARTIAL-LIST' }],
    }),
    listFavoriteBars: build.query<BarSummary[], void>({
      query: () => '/bars/favorites',
      providesTags: ['BarFavorites'],
    }),
    getBar: build.query<BarDetail, number>({
      query: (id) => `/bars/${id}`,
      providesTags: (_r, _e, id) => [{ type: 'Bar', id }],
    }),
    favoriteBar: build.mutation<void, number>({
      query: (id) => ({ url: `/bars/${id}/favorite`, method: 'POST' }),
      invalidatesTags: (_r, _e, id) => [
        { type: 'Bar', id },
        'BarFavorites',
        { type: 'BarList', id: 'PARTIAL-LIST' },
      ],
    }),
    unfavoriteBar: build.mutation<void, number>({
      query: (id) => ({ url: `/bars/${id}/favorite`, method: 'DELETE' }),
      invalidatesTags: (_r, _e, id) => [
        { type: 'Bar', id },
        'BarFavorites',
        { type: 'BarList', id: 'PARTIAL-LIST' },
      ],
    }),
    upsertReview: build.mutation<BarReview, BarReviewCreate>({
      query: ({ bar_id, ...body }) => ({
        url: `/bars/${bar_id}/review`,
        method: 'PUT',
        body,
      }),
      invalidatesTags: (_r, _e, { bar_id }) => [
        { type: 'Bar', id: bar_id },
        { type: 'BarList', id: 'PARTIAL-LIST' },
      ],
    }),
    deleteReview: build.mutation<void, number>({
      query: (bar_id) => ({
        url: `/bars/${bar_id}/review`,
        method: 'DELETE',
      }),
      invalidatesTags: (_r, _e, bar_id) => [
        { type: 'Bar', id: bar_id },
        { type: 'BarList', id: 'PARTIAL-LIST' },
      ],
    }),
  }),
});

export const {
  useListBarsQuery,
  useListFavoriteBarsQuery,
  useGetBarQuery,
  useFavoriteBarMutation,
  useUnfavoriteBarMutation,
  useUpsertReviewMutation,
  useDeleteReviewMutation,
} = barsApi;
