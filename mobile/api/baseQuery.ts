/**
 * RTK Query baseQuery with automatic refresh-token rotation.
 *
 * Behaviour:
 *  1. Every outbound request gets `Authorization: Bearer <accessToken>` if
 *     one is present in Redux.
 *  2. On a 401, we serialise a single /auth/refresh call across all in-flight
 *     queries (so 10 concurrent 401s don't fire 10 refresh requests), then
 *     retry the original request once.
 *  3. If the refresh fails (or there's no refresh token), we dispatch
 *     `signedOut` and let the root layout redirect to the auth flow.
 *
 * Used by every RTK Query slice via the `api/index.ts` re-export.
 */

import {
  BaseQueryFn,
  FetchArgs,
  FetchBaseQueryError,
  fetchBaseQuery,
} from '@reduxjs/toolkit/query/react';

import { API_BASE_URL } from '../lib/config';
import { tokenStorage } from '../lib/tokenStorage';
import type { RootState } from '../store';
import {
  sessionEstablished,
  signedOut,
  tokensRotated,
} from '../store/authSlice';

// ──────────────────────────────────────────────────────────────────────────────
// Plain fetcher — used both as the default and inside the refresh path.
// ──────────────────────────────────────────────────────────────────────────────
const rawBaseQuery = fetchBaseQuery({
  baseUrl: API_BASE_URL,
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.accessToken;
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    return headers;
  },
});

// ──────────────────────────────────────────────────────────────────────────────
// Single-flight refresh
// ──────────────────────────────────────────────────────────────────────────────
let refreshPromise: Promise<boolean> | null = null;

async function refreshAccessToken(
  refreshToken: string,
  api: Parameters<BaseQueryFn>[1],
  extra: Parameters<BaseQueryFn>[2],
): Promise<boolean> {
  const result = await rawBaseQuery(
    {
      url: '/auth/refresh',
      method: 'POST',
      body: { refresh_token: refreshToken },
    },
    api,
    extra,
  );

  if (result.error) return false;
  const data = result.data as {
    access_token: string;
    refresh_token: string;
  };
  if (!data?.access_token || !data?.refresh_token) return false;

  api.dispatch(
    tokensRotated({
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
    }),
  );
  await tokenStorage.saveRefresh(data.refresh_token);
  return true;
}

// ──────────────────────────────────────────────────────────────────────────────
// The actual baseQuery exported to RTK Query
// ──────────────────────────────────────────────────────────────────────────────
export const baseQueryWithRefresh: BaseQueryFn<
  string | FetchArgs,
  unknown,
  FetchBaseQueryError
> = async (args, api, extra) => {
  let result = await rawBaseQuery(args, api, extra);

  if (result.error?.status === 401) {
    const refreshToken = (api.getState() as RootState).auth.refreshToken;
    if (!refreshToken) {
      api.dispatch(signedOut());
      await tokenStorage.clearRefresh();
      return result;
    }

    // De-duplicate concurrent refresh attempts.
    if (!refreshPromise) {
      refreshPromise = refreshAccessToken(refreshToken, api, extra).finally(
        () => {
          refreshPromise = null;
        },
      );
    }
    const refreshed = await refreshPromise;
    if (refreshed) {
      result = await rawBaseQuery(args, api, extra);
    } else {
      api.dispatch(signedOut());
      await tokenStorage.clearRefresh();
    }
  }

  return result;
};

/**
 * Programmatic helper for the boot flow (`app/_layout.tsx`).
 * Used outside of RTK Query — we don't have a query to run yet, we just want
 * to bring our saved refresh token back to life.
 */
export async function bootstrapSession(
  api: Parameters<BaseQueryFn>[1],
  extra: Parameters<BaseQueryFn>[2],
): Promise<boolean> {
  const stored = await tokenStorage.loadRefresh();
  if (!stored) return false;
  const ok = await refreshAccessToken(stored, api, extra);
  if (!ok) {
    await tokenStorage.clearRefresh();
    return false;
  }

  // Once we have an access token, fetch /auth/me to hydrate the user.
  const meResult = await rawBaseQuery({ url: '/auth/me' }, api, extra);
  if (meResult.error) return false;

  // Push user + tokens into one action so subscribers see one consistent state.
  const state = (api.getState() as RootState).auth;
  if (state.accessToken && state.refreshToken) {
    api.dispatch(
      sessionEstablished({
        user: meResult.data as any,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    );
  }
  return true;
}
