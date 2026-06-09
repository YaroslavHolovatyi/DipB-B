/**
 * Runtime config.
 *
 * In Expo, environment variables prefixed with `EXPO_PUBLIC_` are inlined at
 * build time. When developing on a real device, set EXPO_PUBLIC_API_BASE_URL
 * to your laptop's LAN IP (e.g. http://192.168.0.42:8000) — `localhost` won't
 * resolve from the phone.
 */

import Constants from 'expo-constants';

function hostFromExpo(): string | null {
  // Expo dev server URL, e.g. exp://192.168.0.42:8081
  const hostUri =
    (Constants.expoConfig as any)?.hostUri ??
    (Constants as any)?.manifest2?.extra?.expoClient?.hostUri ??
    (Constants as any)?.manifest?.debuggerHost;
  if (typeof hostUri !== 'string') return null;
  const host = hostUri.split(':')[0];
  return host || null;
}

const FALLBACK_HOST = hostFromExpo() ?? 'localhost';

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ?? `http://${FALLBACK_HOST}:8000`;

export const WS_BASE_URL =
  process.env.EXPO_PUBLIC_WS_BASE_URL ??
  API_BASE_URL.replace(/^http/, 'ws');
