/**
 * Persistent refresh-token storage.
 *
 * The refresh token lives in the iOS Keychain / Android EncryptedSharedPreferences
 * via expo-secure-store. The access token is held only in Redux memory — it's
 * short-lived and we don't want to write it to disk on every refresh.
 *
 * On web (`SecureStore` unavailable) we fall back to localStorage. Web is not
 * the target platform but this keeps `expo start --web` from crashing during
 * development.
 */

import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const REFRESH_KEY = 'bb_refresh_token';

async function setItem(key: string, value: string): Promise<void> {
  if (Platform.OS === 'web') {
    // eslint-disable-next-line no-undef
    (globalThis as any).localStorage?.setItem(key, value);
    return;
  }
  await SecureStore.setItemAsync(key, value, {
    keychainAccessible: SecureStore.AFTER_FIRST_UNLOCK,
  });
}

async function getItem(key: string): Promise<string | null> {
  if (Platform.OS === 'web') {
    return (globalThis as any).localStorage?.getItem(key) ?? null;
  }
  return SecureStore.getItemAsync(key);
}

async function deleteItem(key: string): Promise<void> {
  if (Platform.OS === 'web') {
    (globalThis as any).localStorage?.removeItem(key);
    return;
  }
  await SecureStore.deleteItemAsync(key);
}

export const tokenStorage = {
  saveRefresh: (token: string) => setItem(REFRESH_KEY, token),
  loadRefresh: () => getItem(REFRESH_KEY),
  clearRefresh: () => deleteItem(REFRESH_KEY),
};
