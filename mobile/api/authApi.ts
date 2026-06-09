/**
 * Auth endpoints — signup / login / refresh (manual) / logout / me.
 *
 * Refresh is normally driven by the baseQuery (auto-rotation on 401). The
 * explicit `refresh` mutation is exposed here mainly for tests and edge cases.
 */

import { api } from './index';
import type { AuthResponse, TokenPair } from './types';
import type { AuthUser } from '../store/authSlice';

interface SignupBody {
  first_name: string;
  last_name?: string | null;
  username: string;
  email: string;
  password: string;
  main_city_id: number;
}

interface LoginBody {
  identifier: string;
  password: string;
}

export const authApi = api.injectEndpoints({
  endpoints: (build) => ({
    signup: build.mutation<AuthResponse, SignupBody>({
      query: (body) => ({ url: '/auth/signup', method: 'POST', body }),
    }),
    login: build.mutation<AuthResponse, LoginBody>({
      query: (body) => ({ url: '/auth/login', method: 'POST', body }),
    }),
    refresh: build.mutation<TokenPair, { refresh_token: string }>({
      query: (body) => ({ url: '/auth/refresh', method: 'POST', body }),
    }),
    logout: build.mutation<void, { refresh_token: string }>({
      query: (body) => ({ url: '/auth/logout', method: 'POST', body }),
    }),
    me: build.query<AuthUser, void>({
      query: () => '/auth/me',
      providesTags: ['User'],
    }),
  }),
});

export const {
  useSignupMutation,
  useLoginMutation,
  useRefreshMutation,
  useLogoutMutation,
  useMeQuery,
  useLazyMeQuery,
} = authApi;
