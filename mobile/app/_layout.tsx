/**
 * Root layout.
 *
 * Responsibilities:
 *   1. Load custom fonts (Fraunces / Plus Jakarta / JetBrains Mono).
 *   2. On first mount, restore the refresh token from secure storage and
 *      hit /auth/refresh + /auth/me to bring the session back. This runs
 *      while the splash screen is still up so the user never sees a flicker.
 *   3. Gate routes — `(tabs)` are only reachable when authenticated;
 *      `(auth)` only when unauthenticated. Expo Router handles the actual
 *      navigation; we just `router.replace` on transitions.
 *   4. Open the WebSocket connection while authenticated.
 */

import { useEffect } from 'react';
import { MedievalSharp_400Regular } from '@expo-google-fonts/medievalsharp';
import {
  JetBrainsMono_500Medium,
  JetBrainsMono_700Bold,
} from '@expo-google-fonts/jetbrains-mono';
import {
  PlusJakartaSans_400Regular,
  PlusJakartaSans_600SemiBold,
  PlusJakartaSans_700Bold,
} from '@expo-google-fonts/plus-jakarta-sans';
import { useFonts } from 'expo-font';
import { Stack, useRouter, useSegments } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { Provider } from 'react-redux';
import { TamaguiProvider } from 'tamagui';

import { bootstrapSession } from '../api/baseQuery';
import { registerForPush } from '../lib/push';
import { ws } from '../lib/ws';
import { tamaguiConfig } from '../theme/tamagui.config';
import {
  AppDispatch,
  store,
  useAppDispatch,
  useAppSelector,
} from '../store';
import { bootStarted, signedOut } from '../store/authSlice';

SplashScreen.preventAutoHideAsync();

// --------------------------------------------------------------------------- //
// Bootstrap + redirect — must live INSIDE <Provider> so it can dispatch.
// --------------------------------------------------------------------------- //
function SessionBootstrap() {
  const dispatch = useAppDispatch();
  const status = useAppSelector((s) => s.auth.status);
  const accessToken = useAppSelector((s) => s.auth.accessToken);
  const needsRace = useAppSelector(
    (s) => s.auth.status === 'authenticated' && s.auth.user != null && s.auth.user.race_id == null,
  );
  const router = useRouter();
  const segments = useSegments();

  // On first mount, try to restore the session.
  useEffect(() => {
    let cancelled = false;
    async function boot() {
      dispatch(bootStarted());
      const fakeApi = {
        dispatch,
        getState: store.getState,
        extra: undefined,
        endpoint: 'bootstrap',
        type: 'query' as const,
        forced: undefined,
        signal: new AbortController().signal,
        abort: () => {},
      };
      const ok = await bootstrapSession(fakeApi as any, {});
      if (cancelled) return;
      if (!ok) dispatch(signedOut());
    }
    boot();
    return () => {
      cancelled = true;
    };
  }, [dispatch]);

  useEffect(() => {
    ws.attach(dispatch as AppDispatch, store.getState as () => any);
    if (status === 'authenticated' && accessToken) {
      ws.connect();
      registerForPush(dispatch as AppDispatch);
      return () => ws.disconnect();
    }
    return undefined;
  }, [status, accessToken, dispatch]);

  useEffect(() => {
    if (status === 'idle' || status === 'restoring') return;
    const inAuthGroup = segments[0] === '(auth)';
    const inQuiz = (segments[0] as string) === 'quiz';
    // Onboarding gate: an authenticated user without a race must take the quiz
    // before reaching the app. This takes priority over the tabs redirect.
    if (needsRace && !inQuiz) {
      router.replace('/quiz' as never);
    } else if (status === 'authenticated' && inAuthGroup && !needsRace) {
      router.replace('/(tabs)');
    } else if (status === 'unauthenticated' && !inAuthGroup) {
      router.replace('/(auth)');
    }
  }, [status, segments, router, needsRace]);

  return null;
}

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    MedievalSharp_400Regular,
    PlusJakartaSans_400Regular,
    PlusJakartaSans_600SemiBold,
    PlusJakartaSans_700Bold,
    JetBrainsMono_500Medium,
    JetBrainsMono_700Bold,
  });

  useEffect(() => {
    if (fontsLoaded || fontError) SplashScreen.hideAsync();
  }, [fontsLoaded, fontError]);

  if (!fontsLoaded && !fontError) return null;

  return (
    <Provider store={store}>
      <TamaguiProvider config={tamaguiConfig} defaultTheme="dark">
        <SessionBootstrap />
        <Stack screenOptions={{ headerShown: false, animation: 'fade' }}>
          <Stack.Screen name="(auth)" />
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="quiz/index" options={{ gestureEnabled: false }} />
          <Stack.Screen name="profile/index" />
          <Stack.Screen name="profile/edit" options={{ presentation: 'modal' }} />
          <Stack.Screen name="friends" />
          <Stack.Screen name="tavern/[sessionId]" />
          <Stack.Screen name="notifications" options={{ presentation: 'modal' }} />
          <Stack.Screen name="bars/[id]" />
          <Stack.Screen name="raids/[id]" />
          <Stack.Screen name="raids/new" options={{ presentation: 'modal' }} />
          <Stack.Screen name="party/index" />
          <Stack.Screen name="party/[id]" />
          <Stack.Screen name="party/new" options={{ presentation: 'modal' }} />
          <Stack.Screen name="chat/[id]" />
          <Stack.Screen name="checks/[id]" />
        </Stack>
      </TamaguiProvider>
    </Provider>
  );
}
