/**
 * Sign Up Screen — wired to POST /auth/signup.
 *
 * The city field is a chip-row populated from /reference/cities. Lviv is
 * pre-selected since it's the only seeded city, but the picker is flexible.
 */

import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useCallback, useMemo, useState } from 'react';
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

import { useSignupMutation } from '../../api/authApi';
import { useListCitiesQuery } from '../../api/referenceApi';
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
  chipBg: '#1E1E38',
  chipBorder: 'rgba(255,255,255,0.10)',
  chipBgActive: '#6366F1',
};

type FormErrors = Partial<
  Record<'firstName' | 'email' | 'username' | 'password' | 'city' | 'general', string>
>;

function validate(fields: {
  firstName: string;
  email: string;
  username: string;
  password: string;
  cityId: number | null;
}): FormErrors {
  const err: FormErrors = {};
  if (!fields.firstName.trim()) err.firstName = 'First name is required';
  if (!fields.email.trim()) err.email = 'Email is required';
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(fields.email))
    err.email = 'Enter a valid email address';
  if (!fields.username.trim()) err.username = 'Username is required';
  else if (fields.username.length < 3)
    err.username = 'Username must be at least 3 characters';
  else if (!/^[a-zA-Z0-9_.-]+$/.test(fields.username))
    err.username = 'Only letters, numbers, dot, dash, underscore';
  if (!fields.password) err.password = 'Password is required';
  else if (fields.password.length < 8)
    err.password = 'Password must be at least 8 characters';
  if (fields.cityId == null) err.city = 'Pick your main city';
  return err;
}

export default function SignUpScreen() {
  const dispatch = useAppDispatch();
  const { data: cities = [], isLoading: citiesLoading, isError: citiesError } = useListCitiesQuery();
  const [signup, { isLoading }] = useSignupMutation();

  const [firstName, setFirstName] = useState('');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [cityId, setCityId] = useState<number | null>(null);
  const [errors, setErrors] = useState<FormErrors>({});

  // Pre-select the first city once they load.
  const defaultCityId = useMemo(
    () => cities.find((c) => c.slug === 'lviv')?.id ?? cities[0]?.id ?? null,
    [cities],
  );
  if (cityId == null && defaultCityId != null) setCityId(defaultCityId);

  const handleSubmit = useCallback(async () => {
    const errs = validate({ firstName, email, username, password, cityId });
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    try {
      const response = await signup({
        first_name: firstName.trim(),
        username: username.trim(),
        email: email.trim().toLowerCase(),
        password,
        main_city_id: cityId!,
      }).unwrap();
      await tokenStorage.saveRefresh(response.tokens.refresh_token);
      dispatch(
        sessionEstablished({
          user: response.user,
          accessToken: response.tokens.access_token,
          refreshToken: response.tokens.refresh_token,
        }),
      );
    } catch (e: any) {
      const detail =
        e?.data?.detail ?? 'Sign-up failed. Please try a different email or username.';
      setErrors({ general: String(detail) });
    }
  }, [firstName, email, username, password, cityId, signup, dispatch]);

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
              <Ionicons name="chevron-back" size={20} color="#94A3B8" />
              <Text style={s.backLabel}>Back</Text>
            </TouchableOpacity>

            <View style={s.header}>
              <Ionicons name="shield" size={40} color="#D99A1C" style={s.headerIcon} />
              <Text style={s.title}>Forge Your Legend</Text>
              <Text style={s.subtitle}>Join the order. Roll for friendship.</Text>
            </View>

            <View style={s.card}>
              <AuthInput
                label="First name"
                placeholder="Yaroslav"
                value={firstName}
                onChangeText={setFirstName}
                error={errors.firstName}
                autoCapitalize="words"
                returnKeyType="next"
              />

              <AuthInput
                label="Email"
                placeholder="you@example.com"
                value={email}
                onChangeText={setEmail}
                error={errors.email}
                autoCapitalize="none"
                keyboardType="email-address"
                returnKeyType="next"
                textContentType="emailAddress"
              />

              <AuthInput
                label="Username"
                placeholder="3+ chars, no spaces"
                value={username}
                onChangeText={setUsername}
                error={errors.username}
                autoCapitalize="none"
                returnKeyType="next"
                textContentType="username"
              />

              <AuthInput
                label="Password"
                placeholder="At least 8 characters"
                value={password}
                onChangeText={setPassword}
                error={errors.password}
                isPassword
                returnKeyType="done"
                textContentType="newPassword"
              />

              {/* City picker — chip row */}
              <View>
                <Text style={s.fieldLabel}>City</Text>
                {citiesLoading ? (
                  <ActivityIndicator color={DC.brandLight} style={{ marginTop: 8 }} />
                ) : citiesError ? (
                  <Text style={s.cityUnavailable}>
                    Could not load cities — make sure the backend is running.
                  </Text>
                ) : cities.length === 0 ? (
                  <Text style={s.cityUnavailable}>
                    No cities available yet. Run the database seed first.
                  </Text>
                ) : (
                  <ScrollView
                    horizontal
                    showsHorizontalScrollIndicator={false}
                    contentContainerStyle={s.chipRow}
                  >
                    {cities.map((c) => {
                      const active = cityId === c.id;
                      return (
                        <TouchableOpacity
                          key={c.id}
                          onPress={() => setCityId(c.id)}
                          activeOpacity={0.8}
                          style={[s.chip, active && s.chipActive]}
                        >
                          <Text style={[s.chipText, active && s.chipTextActive]}>{c.name}</Text>
                        </TouchableOpacity>
                      );
                    })}
                  </ScrollView>
                )}
                {errors.city && <Text style={s.errorText}>{errors.city}</Text>}
              </View>
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
                  <Text style={s.primaryBtnText}>Create Account</Text>
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
              onPress={() => router.replace('/(auth)/sign-in')}
            >
              <Text style={s.switchText}>Already have an account? </Text>
              <Text style={s.switchLink}>Sign in</Text>
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

  header: { alignItems: 'center', paddingTop: 16, paddingBottom: 24, gap: 6 },
  headerIcon: { marginBottom: 4 },
  title: {
    fontFamily: F.headingBold, fontSize: 28, color: DC.gold, textAlign: 'center', letterSpacing: -0.5,
    ...Platform.select({ ios: { textShadowColor: 'rgba(245,158,11,0.35)', textShadowOffset: { width: 0, height: 0 }, textShadowRadius: 14 } }),
  },
  subtitle: { fontFamily: F.bodyRegular, fontSize: 15, color: DC.textSecondary, textAlign: 'center' },

  card: { backgroundColor: DC.card, borderRadius: 20, borderWidth: 1, borderColor: DC.cardBorder, padding: 20, gap: 16, marginBottom: 20 },

  fieldLabel: { fontFamily: F.bodySemiBold, fontSize: 13, color: DC.textSecondary, marginBottom: 8, letterSpacing: 0.3 },

  chipRow: { gap: 8, paddingVertical: 2 },
  chip: {
    backgroundColor: DC.chipBg, borderColor: DC.chipBorder, borderWidth: 1,
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 999,
  },
  chipActive: { backgroundColor: DC.chipBgActive, borderColor: DC.chipBgActive },
  chipText: { fontFamily: F.bodySemiBold, fontSize: 13, color: DC.textSecondary },
  chipTextActive: { color: '#FFFFFF' },

  cityUnavailable: { fontFamily: F.bodyRegular, fontSize: 13, color: DC.textMuted, marginTop: 4, fontStyle: 'italic' },
  errorText: { fontFamily: F.bodyRegular, fontSize: 12, color: DC.error, marginTop: 6 },
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
