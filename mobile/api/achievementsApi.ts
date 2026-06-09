/** Achievements. */

import { api } from './index';
import type { Achievement, UserAchievement } from './types';

export const achievementsApi = api.injectEndpoints({
  endpoints: (build) => ({
    listAchievements: build.query<Achievement[], void>({
      query: () => '/achievements',
      providesTags: ['Achievement'],
    }),
    myAchievements: build.query<UserAchievement[], void>({
      query: () => '/achievements/me',
      providesTags: ['UserAchievement'],
    }),
    myPoints: build.query<{ points: number }, void>({
      query: () => '/achievements/me/points',
      providesTags: ['UserAchievement'],
    }),
  }),
});

export const {
  useListAchievementsQuery,
  useMyAchievementsQuery,
  useMyPointsQuery,
} = achievementsApi;
