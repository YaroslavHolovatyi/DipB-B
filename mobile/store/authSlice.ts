/**
 * Redux slice for authentication state.
 *
 * - `accessToken` is held in Redux memory only (never persisted).
 * - The refresh token is persisted via `tokenStorage` (expo-secure-store) so
 *   we can transparently log the user back in on app launch.
 * - `user` is the `UserPublic` payload from /auth/me — kept here so the UI
 *   can render avatars / names without spinning a query every screen.
 * - `status` drives the root layout's redirect logic:
 *     'idle'         — never touched, show auth flow
 *     'restoring'    — boot-time check in progress (we have a saved refresh
 *                      token and are calling /auth/refresh)
 *     'authenticated'— we have a valid access token + user
 *     'unauthenticated' — no session, show auth flow
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface AuthUser {
  id: number;
  first_name: string;
  last_name: string | null;
  username: string;
  email: string;
  avatar_url: string | null;
  bio: string | null;
  main_city_id: number;
  race_id: number | null;
  role: string;
  is_active: boolean;
  social_rating: number;
  events_attended: number;
  events_ditched: number;
}

export type AuthStatus =
  | 'idle'
  | 'restoring'
  | 'authenticated'
  | 'unauthenticated';

export interface AuthState {
  status: AuthStatus;
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
}

const initialState: AuthState = {
  status: 'idle',
  user: null,
  accessToken: null,
  refreshToken: null,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    /** Set to 'restoring' before we call /auth/refresh at app launch. */
    bootStarted(state) {
      state.status = 'restoring';
    },
    /** Used by login / signup / refresh — installs the full session. */
    sessionEstablished(
      state,
      action: PayloadAction<{
        user: AuthUser;
        accessToken: string;
        refreshToken: string;
      }>,
    ) {
      state.status = 'authenticated';
      state.user = action.payload.user;
      state.accessToken = action.payload.accessToken;
      state.refreshToken = action.payload.refreshToken;
    },
    /** Used by the silent refresh — same tokens, no user reload. */
    tokensRotated(
      state,
      action: PayloadAction<{ accessToken: string; refreshToken: string }>,
    ) {
      state.accessToken = action.payload.accessToken;
      state.refreshToken = action.payload.refreshToken;
    },
    /** Patch the in-memory user object after a profile edit. */
    userUpdated(state, action: PayloadAction<AuthUser>) {
      state.user = action.payload;
    },
    /** Wipe everything — logout or unrecoverable 401. */
    signedOut(state) {
      state.status = 'unauthenticated';
      state.user = null;
      state.accessToken = null;
      state.refreshToken = null;
    },
  },
});

export const {
  bootStarted,
  sessionEstablished,
  tokensRotated,
  userUpdated,
  signedOut,
} = authSlice.actions;
export const authReducer = authSlice.reducer;
