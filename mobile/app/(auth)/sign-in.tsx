/**
 * Sign In Screen — wired to POST /auth/login.
 *
 * Accepts either email OR username in the same field (backend's `identifier`).
 * On success, hydrates Redux auth state and saves the refresh token; the root
 * layout's redirect effect then bounces us to (tabs).
 */

import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useLoginMutation } from '../../api/authApi';
import { AuthInput } from '../../components/auth/AuthInput';
import { tokenStorage } from '../../lib/tokenStorage';
import { useAppDispatch } from '../../store';
import { sessionEstablished } from '../../store/authSlice';
import { F } from '../../theme/styleHelpers';

const DC = {
  bg: '#0A0A1A',
  gradStart: '#0A0A1A',
  gradEnd: '#1E0E3E',
  card: '#13132B',
  cardBorder: 'rgba(255,255,255,0.07)',
  textPrimary: '#F1F5F9',
  textSecondary: '#94A3B8',
  textMuted: '#475569',
  brand: '#6366F1',
  brandLight: '#818CF8',
  gold: '#F59E0B',
  error: '#F87171',
  divider: 'rgba(255,255,255,0.08)',
};

type FormErrors = Partial<Record<'identifier' | 'password' | 'general', string>>;

function validate(identifier: string, password: string): FormErrors {
  const err: FormErrors = {};
  if (!identifier.trim()) err.identifier = 'Email or username is required';
  if (!password) err.password = 'Password is required';
  else if (password.length < 8) err.password = 'Password must be at least 8 characters';
  return err;
}

export default function SignInScreen() {
  const dispatch = useAppDispatch();
  const [login, { isLoading }] = useLoginMutation();

  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});

  const handleSubmit = useCallback(async () => {
    const errs = validate(identifier, password);
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    try {
      const response = await login({ identifier: identifier.trim(), password }).unwrap();
      await tokenStorage.saveRefresh(response.tokens.refresh_token);
      dispatch(
        sessionEstablished({
          user: response.user,
          accessToken: response.tokens.access_token,
          refreshToken: response.tokens.refresh_token,
        }),
      );
      // The root layout's redirect effect will move us into (tabs).
    } catch (e: any) {
      const detail =
        e?.data?.detail ?? 'Could not sign in. Check your credentials and try again.';
      setErrors({ general: String(detail) });
    }
  }, [identifier, password, login, dispatch]);

  return (
    <View style={s.root}>
      <StatusBar style="light" />

      <LinearGradient
        colors={[DC.gradStart, DC.gradEnd]}
        style={StyleSheet.absoluteFill}
        start={{ x: 0.3, y: 0 }}
        end={{ x: 0.7, y: 1 }}
      />

      <SafeAreaView style={s.safe} edges={['top', 'bottom']}>
        <KeyboardAvoidingView
          style={s.kav}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <ScrollView
            contentContainerStyle={s.scroll}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
          >
            <TouchableOpacity
              style={s.backBtn}
              onPress={() => router.back()}
              activeOpacity={0.7}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Text style={s.backArrow}>←</Text>
              <Text style={s.backLabel}>Back</Text>
            </TouchableOpacity>

            <View style={s.header}>
              <Text style={s.emoji}>⚔️</Text>
              <Text style={s.title}>Welcome Back</Text>
              <Text style={s.subtitle}>Your tavern awaits, adventurer.</Text>
            </View>

            <View style={s.card}>
              <AuthInput
                label="Email or username"
                placeholder="you@example.com or your_name"
                value={identifier}
                onChangeText={setIdentifier}
                error={errors.identifier}
                autoCapitalize="none"
                returnKeyType="next"
                textContentType="username"
              />

              <AuthInput
                label="Password"
                placeholder="Your password"
                value={password}
                onChangeText={setPassword}
                error={errors.password}
                isPassword
                returnKeyType="done"
                onSubmitEditing={handleSubmit}
                textContentType="password"
              />
            </View>

            {errors.general && <Text style={s.generalError}>{errors.general}</Text>}

            <TouchableOpacity
              activeOpacity={0.85}
              onPress={handleSubmit}
              disabled={isLoading}
              style={s.primaryBtnWrap}
            >
              <LinearGradient
                colors={isLoading ? ['#4B4BC8', '#4B4BC8'] : ['#7C3AED', '#6366F1', '#4F46E5']}
                style={s.primaryBtn}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
              >
                {isLoading ? (
                  <ActivityIndicator color="#FFFFFF" size="small" />
                ) : (
                  <Text style={s.primaryBtnText}>Sign In</Text>
                )}
              </LinearGradient>
            </TouchableOpacity>

            <View style={s.dividerRow}>
              <View style={s.dividerLine} />
              <Text style={s.dividerText}>or</Text>
              <View style={s.dividerLine} />
            </View>

            <TouchableOpacity
              style={s.switchRow}
              activeOpacity={0.7}
              onPress={() => router.replace('/(auth)/sign-up')}
            >
              <Text style={s.switchText}>New to B&B? </Text>
              <Text style={s.switchLink}>Create an account</Text>
            </TouchableOpacity>

            <View style={{ height: 16 }} />
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: DC.bg },
  safe: { flex: 1 },
  kav: { flex: 1 },
  scroll: { paddingHorizontal: 24, paddingBottom: 8 },

  backBtn: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingTop: 16, paddingBottom: 8, alignSelf: 'flex-start' },
  backArrow: { fontFamily: F.bodyBold, fontSize: 20, color: DC.textSecondary, lineHeight: 24 },
  backLabel: { fontFamily: F.bodySemiBold, fontSize: 15, color: DC.textSecondary },

  header: { alignItems: 'center', paddingTop: 24, paddingBottom: 32, gap: 6 },
  emoji: { fontSize: 40, marginBottom: 4 },
  title: {
    fontFamily: F.headingBold, fontSize: 30, color: DC.gold, textAlign: 'center',
    letterSpacing: -0.5,
    ...Platform.select({
      ios: { textShadowColor: 'rgba(245,158,11,0.35)', textShadowOffset: { width: 0, height: 0 }, textShadowRadius: 14 },
    }),
  },
  subtitle: { fontFamily: F.bodyRegular, fontSize: 15, color: DC.textSecondary, textAlign: 'center' },

  card: { backgroundColor: DC.card, borderRadius: 20, borderWidth: 1, borderColor: DC.cardBorder, padding: 20, gap: 16, marginBottom: 20 },

  generalError: {
    fontFamily: F.bodySemiBold, fontSize: 14, color: DC.error,
    textAlign: 'center', marginBottom: 12,
  },

  primaryBtnWrap: {
    borderRadius: 16, overflow: 'hidden', marginBottom: 20,
    ...Platform.select({
      ios: { shadowColor: '#6366F1', shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.4, shadowRadius: 14 },
      android: { elevation: 8 },
    }),
  },
  primaryBtn: { height: 56, alignItems: 'center', justifyContent: 'center', borderRadius: 16 },
  primaryBtnText: { fontFamily: F.bodyBold, fontSize: 17, color: '#FFFFFF', letterSpacing: 0.2 },

  dividerRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 20 },
  dividerLine: { flex: 1, height: 1, backgroundColor: DC.divider },
  dividerText: { fontFamily: F.bodyRegular, fontSize: 13, color: DC.textMuted },

  switchRow: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center' },
  switchText: { fontFamily: F.bodyRegular, fontSize: 14, color: DC.textSecondary },
  switchLink: { fontFamily: F.bodyBold, fontSize: 14, color: DC.brandLight },
});
