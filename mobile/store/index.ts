/**
 * Root Redux store.
 *
 * - `auth`     — locally managed Redux slice (user, tokens, status).
 * - `api`      — single RTK Query instance (every domain injects endpoints).
 *
 * Importing the API slices for their side effect (`injectEndpoints` registers
 * them on the `api` slice) keeps the store wiring clean even though the
 * imports look unused.
 */

import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';

import { api } from '../api';
import { authReducer } from './authSlice';

// Side-effect imports — register endpoints on the shared `api` slice.
import '../api/authApi';
import '../api/referenceApi';
import '../api/usersApi';
import '../api/barsApi';
import '../api/quizApi';
import '../api/friendsApi';
import '../api/raidsApi';
import '../api/notificationsApi';
import '../api/checksApi';
import '../api/achievementsApi';
import '../api/chatApi';
import '../api/tavernApi';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    [api.reducerPath]: api.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }).concat(api.middleware),
});

// Enables refetchOnFocus / refetchOnReconnect on the RTK Query subscribers.
setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export const useAppDispatch: () => AppDispatch = useDispatch;
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
