/**
 * Edit Profile — self-service via PATCH /users/me.
 *
 * Editable: first name, last name, main city (chip row from /reference/cities).
 * On save we get the fresh UserPublic back, push it into the Redux user
 * (`userUpdated`) so every screen reflects the change immediately, then close.
 *
 * Reached from Profile → "Edit". Presented as a modal (see app/_layout.tsx).
 */

import { router, Stack } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useListCitiesQuery, useListInterestsQuery } from '../../api/referenceApi';
import {
  useMyInterestsQuery,
  useSetMyInterestsMutation,
  useUpdateMeMutation,
} from '../../api/usersApi';
import { useAppDispatch, useAppSelector } from '../../store';
import { userUpdated } from '../../store/authSlice';
import { C, F } from '../../theme/styleHelpers';

export default function EditProfileScreen() {
  const dispatch = useAppDispatch();
  const user = useAppSelector((s) => s.auth.user);

  const { data: cities = [], isLoading: citiesLoading } = useListCitiesQuery();
  const { data: interests = [], isLoading: interestsLoading } = useListInterestsQuery();
  const { data: myInterests } = useMyInterestsQuery();
  const [updateMe, { isLoading: saving }] = useUpdateMeMutation();
  const [setMyInterests, { isLoading: savingInterests }] = useSetMyInterestsMutation();

  const [firstName, setFirstName] = useState(user?.first_name ?? '');
  const [lastName, setLastName] = useState(user?.last_name ?? '');
  const [bio, setBio] = useState(user?.bio ?? '');
  const [cityId, setCityId] = useState<number | null>(user?.main_city_id ?? null);
  const [selectedInterests, setSelectedInterests] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Seed the selected-interests state once the server list arrives.
  const initialInterests = useMemo(
    () => (myInterests ?? []).map((i) => i.id).sort((a, b) => a - b),
    [myInterests],
  );
  useEffect(() => {
    if (myInterests) setSelectedInterests(initialInterests);
  }, [myInterests, initialInterests]);

  const toggleInterest = (id: number) =>
    setSelectedInterests((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );

  const interestsDirty = useMemo(() => {
    const sorted = [...selectedInterests].sort((a, b) => a - b);
    return JSON.stringify(sorted) !== JSON.stringify(initialInterests);
  }, [selectedInterests, initialInterests]);

  const dirty = useMemo(
    () =>
      firstName.trim() !== (user?.first_name ?? '') ||
      (lastName.trim() || null) !== (user?.last_name ?? null) ||
      (bio.trim() || null) !== (user?.bio ?? null) ||
      cityId !== (user?.main_city_id ?? null) ||
      interestsDirty,
    [firstName, lastName, bio, cityId, interestsDirty, user],
  );

  const busy = saving || savingInterests;

  const save = async () => {
    setError(null);
    if (!firstName.trim()) {
      setError('First name is required.');
      return;
    }
    try {
      const updated = await updateMe({
        first_name: firstName.trim(),
        last_name: lastName.trim() || null,
        bio: bio.trim() || null,
        main_city_id: cityId ?? undefined,
      }).unwrap();
      if (interestsDirty) {
        await setMyInterests(selectedInterests).unwrap();
      }
      dispatch(userUpdated(updated));
      router.back();
    } catch (e: any) {
      setError(String(e?.data?.detail ?? 'Could not save your profile. Please try again.'));
    }
  };

  if (!user) {
    return (
      <SafeAreaView style={s.safe}>
        <ActivityIndicator style={{ marginTop: 40 }} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={s.safe} edges={['top', 'bottom']}>
      <Stack.Screen options={{ headerShown: false }} />

      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()} hitSlop={8} activeOpacity={0.7}>
          <Text style={s.cancel}>Cancel</Text>
        </TouchableOpacity>
        <Text style={s.title}>Edit Profile</Text>
        <TouchableOpacity
          onPress={save}
          disabled={!dirty || busy}
          hitSlop={8}
          activeOpacity={0.7}
        >
          {busy ? (
            <ActivityIndicator color={C.brandPrimary} />
          ) : (
            <Text style={[s.save, (!dirty || busy) && s.saveDisabled]}>Save</Text>
          )}
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={s.body} keyboardShouldPersistTaps="handled">
          <Text style={s.label}>First name</Text>
          <TextInput
            value={firstName}
            onChangeText={setFirstName}
            placeholder="First name"
            placeholderTextColor={C.textSecondary}
            style={s.input}
            autoCapitalize="words"
            returnKeyType="next"
          />

          <Text style={s.label}>Last name</Text>
          <TextInput
            value={lastName}
            onChangeText={setLastName}
            placeholder="(optional)"
            placeholderTextColor={C.textSecondary}
            style={s.input}
            autoCapitalize="words"
            returnKeyType="done"
          />

          <Text style={s.label}>About you</Text>
          <TextInput
            value={bio}
            onChangeText={setBio}
            placeholder="A short intro — what you're into, what you're looking for…"
            placeholderTextColor={C.textSecondary}
            style={[s.input, s.bioInput]}
            multiline
            maxLength={500}
            textAlignVertical="top"
          />
          <Text style={s.hint}>{bio.length}/500 · shown when you create or join a party.</Text>

          <Text style={s.label}>Username</Text>
          <View style={[s.input, s.inputDisabled]}>
            <Text style={s.disabledText}>@{user.username}</Text>
          </View>
          <Text style={s.hint}>Username and email can&apos;t be changed here.</Text>

          <Text style={s.label}>Main city</Text>
          {citiesLoading ? (
            <ActivityIndicator color={C.brandPrimary} style={{ marginTop: 8 }} />
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

          <Text style={s.label}>Interests</Text>
          <Text style={s.hint}>Pick what you&apos;re into — we use these to match you to parties.</Text>
          {interestsLoading ? (
            <ActivityIndicator color={C.brandPrimary} style={{ marginTop: 8 }} />
          ) : (
            <View style={s.chipWrap}>
              {interests.map((it) => {
                const active = selectedInterests.includes(it.id);
                return (
                  <TouchableOpacity
                    key={it.id}
                    onPress={() => toggleInterest(it.id)}
                    activeOpacity={0.8}
                    style={[s.chip, active && s.chipActive]}
                  >
                    <Text style={[s.chipText, active && s.chipTextActive]}>{it.label}</Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          )}

          {error && <Text style={s.error}>{error}</Text>}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bgBase },

  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 20, paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: C.borderDefault,
  },
  cancel: { fontFamily: F.bodySemiBold, fontSize: 15, color: C.textSecondary },
  title: { fontFamily: F.headingBold, fontSize: 18, color: C.textPrimary },
  save: { fontFamily: F.bodyBold, fontSize: 15, color: C.brandPrimary },
  saveDisabled: { color: C.textDisabled },

  body: { padding: 20, gap: 6 },
  label: {
    fontFamily: F.bodySemiBold, fontSize: 13, color: C.textSecondary,
    marginTop: 14, marginBottom: 6,
  },
  input: {
    fontFamily: F.bodyRegular, fontSize: 15, color: C.textPrimary,
    backgroundColor: C.bgInput, borderRadius: 12,
    borderWidth: 1, borderColor: C.borderDefault,
    paddingHorizontal: 14, paddingVertical: 13,
  },
  inputDisabled: { justifyContent: 'center', backgroundColor: C.bgBase },
  disabledText: { fontFamily: F.bodyRegular, fontSize: 15, color: C.textDisabled },
  hint: { fontFamily: F.bodyRegular, fontSize: 12, color: C.textSecondary, marginTop: 6 },

  bioInput: { minHeight: 96, paddingTop: 12 },

  chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8 },
  chipRow: { gap: 8, paddingVertical: 4 },
  chip: {
    backgroundColor: C.bgCard, borderColor: C.borderDefault, borderWidth: 1,
    paddingHorizontal: 16, paddingVertical: 9, borderRadius: 999,
  },
  chipActive: { backgroundColor: C.brandPrimary, borderColor: C.brandPrimary },
  chipText: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.textSecondary },
  chipTextActive: { color: '#FFFFFF' },

  error: { fontFamily: F.bodySemiBold, fontSize: 13, color: C.error, marginTop: 18, textAlign: 'center' },
});
