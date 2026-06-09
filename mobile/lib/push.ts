/**
 * Expo Push integration.
 *
 * Called once after sign-in: requests notification permission, fetches the
 * `ExponentPushToken[...]` for this device, and POSTs it to
 * `/users/me/push-tokens` so the backend can target this device when the
 * user is offline.
 *
 * Skips silently on the simulator (no push possible) and on web.
 */

import Constants from 'expo-constants';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import type * as NotificationsModule from 'expo-notifications';

import { usersApi } from '../api/usersApi';
import type { AppDispatch } from '../store';

// Push notifications are not supported in Expo Go (SDK 53+).
// Skip all notification setup when running in Expo Go.
const isExpoGo = Constants.appOwnership === 'expo';

// IMPORTANT: load expo-notifications lazily and ONLY outside Expo Go.
// A static `import` loads the module at startup, and in Expo Go (SDK 53+)
// that import itself logs a hard error because push was removed there.
// eslint-disable-next-line @typescript-eslint/no-var-requires
const Notifications: typeof NotificationsModule | null = isExpoGo
  ? null
  : (require('expo-notifications') as typeof NotificationsModule);

// Render incoming pushes as a banner even when the app is foregrounded.
if (Notifications) Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

async function getExpoPushToken(): Promise<string | null> {
  if (!Notifications) return null; // Expo Go — push removed in SDK 53+
  if (Platform.OS === 'web') return null;
  if (!Device.isDevice) return null; // simulator can't receive pushes

  const settings = await Notifications.getPermissionsAsync();
  let status = settings.status;
  if (status !== 'granted') {
    const request = await Notifications.requestPermissionsAsync();
    status = request.status;
  }
  if (status !== 'granted') return null;

  // Android channel — required for any push to show up.
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'Default',
      importance: Notifications.AndroidImportance.DEFAULT,
    });
  }

  const tokenRes = await Notifications.getExpoPushTokenAsync();
  return tokenRes.data ?? null;
}

/** Call once after sign-in. Safe to call again on subsequent launches. */
export async function registerForPush(dispatch: AppDispatch): Promise<void> {
  try {
    const token = await getExpoPushToken();
    if (!token) return;
    const platform =
      Platform.OS === 'ios' ? 'ios' : Platform.OS === 'android' ? 'android' : 'web';
    await dispatch(
      usersApi.endpoints.registerPushToken.initiate({ token, platform }),
    ).unwrap();
  } catch {
    // Push is best-effort; failure is non-fatal.
  }
}
