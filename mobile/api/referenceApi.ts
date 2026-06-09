/**
 * Reference data — cities, vibes, drinks, races. All read-only.
 * Long-cached because the data rarely changes.
 */

import { api } from './index';
import type { City, Drink, Interest, Race, Vibe } from './types';

export const referenceApi = api.injectEndpoints({
  endpoints: (build) => ({
    listCities: build.query<City[], void>({
      query: () => '/reference/cities',
      providesTags: ['Cities'],
    }),
    listVibes: build.query<Vibe[], void>({
      query: () => '/reference/vibes',
      providesTags: ['Vibes'],
    }),
    listDrinks: build.query<Drink[], void>({
      query: () => '/reference/drinks',
      providesTags: ['Drinks'],
    }),
    listRaces: build.query<Race[], void>({
      query: () => '/reference/races',
      providesTags: ['Races'],
    }),
    getRace: build.query<Race, number>({
      query: (id) => `/reference/races/${id}`,
      providesTags: ['Races'],
    }),
    listInterests: build.query<Interest[], void>({
      query: () => '/reference/interests',
      providesTags: ['Interests'],
    }),
  }),
});

export const {
  useListCitiesQuery,
  useListVibesQuery,
  useListDrinksQuery,
  useListRacesQuery,
  useGetRaceQuery,
  useLazyGetRaceQuery,
  useListInterestsQuery,
} = referenceApi;
