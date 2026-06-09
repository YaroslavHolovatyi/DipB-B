import { Stack } from 'expo-router';

export default function AuthLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: '#0A0A1A' },
        animation: 'slide_from_right',
      }}
    >
      <Stack.Screen name="index"    options={{ animation: 'none' }} />
      <Stack.Screen name="sign-in"  />
      <Stack.Screen name="sign-up"  />
    </Stack>
  );
}
