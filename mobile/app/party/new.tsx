/**
 * Create-a-party modal.
 *
 * Parties are interest-matched, so we gate creation on a completed profile:
 * a bio + at least one interest. If either is missing we show a prompt that
 * deep-links to Edit Profile instead of the form.
 *
 * Form: title, description, who-can-join (open / friends), max members, and
 * interest chips (pre-seeded from the user's own interests as a sensible
 * default, since you're usually looking for people who share them).
 */

import { router } from 'expo-router';
import { useEffect, useState } from 'react';
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

import { useListInterestsQuery } from '../../api/referenceApi';
import { useCreatePartyMutation } from '../../api/partiesApi';
import type { DrinkType, PartyVisibility } from '../../api/types';
import { useMyInterestsQuery } from '../../api/usersApi';
import { DRINK_TYPE_OPTIONS } from '../../lib/drinkTypes';
import { useAppSelector } from '../../store';
import { C, F } from '../../theme/styleHelpers';

const VISIBILITY_OPTIONS: { value: PartyVisibility; label: string; hint: string }[] = [
  { value: 'open', label: 'Open', hint: 'Anyone can find and join' },
  { value: 'friends_only', label: 'Friends only', hint: 'Only your friends see it' },
];

export default function NewPartyScreen() {
  const user = useAppSelector((s) => s.auth.user);
  const { data: interests = [], isLoading: interestsLoading } = useListInterestsQuery();
  const { data: myInterests } = useMyInterestsQuery();
  const [createParty, { isLoading }] = useCreatePartyMutation();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [maxMembers, setMaxMembers] = useState('');
  const [visibility, setVisibility] = useState<PartyVisibility>('open');
  const [selected, setSelected] = useState<number[]>([]);
  const [drinks, setDrinks] = useState<DrinkType[]>([]);
  const [error, setError] = useState<string | null>(null);

  const toggleDrink = (t: DrinkType) =>
    setDrinks((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));

  // Default the chips to the user's own interests.
  useEffect(() => {
    if (myInterests && myInterests.length) {
      setSelected(myInterests.map((i) => i.id));
    }
  }, [myInterests]);

  const hasBio = !!(user?.bio && user.bio.trim());
  const hasInterests = (myInterests?.length ?? 0) > 0;
  const profileReady = hasBio && hasInterests;

  const toggle = (id: number) =>
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );

  const submit = async () => {
    setError(null);
    if (!title.trim()) return setError('Title is required');

    let max: number | null = null;
    if (maxMembers.trim()) {
      max = Number(maxMembers.trim());
      if (!Number.isInteger(max) || max < 2 || max > 100) {
        return setError('Max members must be a whole number between 2 and 100');
      }
    }

    try {
      const party = await createParty({
        title: title.trim(),
        description: description.trim() || null,
        max_members: max,
        visibility,
        interest_ids: selected,
        drink_types: drinks,
      }).unwrap();
      router.replace(`/party/${party.id}` as never);
    } catch (e: any) {
      setError(String(e?.data?.detail ?? 'Could not create the party'));
    }
  };

  if (!profileReady) {
    return (
      <SafeAreaView style={s.safe} edges={['top', 'bottom']}>
        <View style={s.header}>
          <TouchableOpacity onPress={() => router.back()}>
            <Text style={s.headerBtn}>Cancel</Text>
          </TouchableOpacity>
          <Text style={s.headerTitle}>🎉 New Party</Text>
          <View style={{ width: 52 }} />
        </View>
        <View style={s.gate}>
          <Text style={s.gateEmoji}>📝</Text>
          <Text style={s.gateTitle}>Finish your profile first</Text>
          <Text style={s.gateBody}>
            Parties match people by interests, so you need
            {!hasBio ? ' a short bio' : ''}
            {!hasBio && !hasInterests ? ' and' : ''}
            {!hasInterests ? ' at least one interest' : ''} before you can host one.
          </Text>
          <TouchableOpacity
            style={s.gateBtn}
            onPress={() => router.replace('/profile/edit' as never)}
            activeOpacity={0.85}
          >
            <Text style={s.gateBtnText}>Edit profile</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={s.safe} edges={['top', 'bottom']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={s.kav}
      >
        <View style={s.header}>
          <TouchableOpacity onPress={() => router.back()}>
            <Text style={s.headerBtn}>Cancel</Text>
          </TouchableOpacity>
          <Text style={s.headerTitle}>🎉 New Party</Text>
          <TouchableOpacity disabled={isLoading} onPress={submit}>
            <Text style={[s.headerBtn, s.headerCta]}>
              {isLoading ? 'Saving…' : 'Create'}
            </Text>
          </TouchableOpacity>
        </View>

        <ScrollView contentContainerStyle={s.content}>
          <Field label="Title">
            <TextInput
              value={title}
              onChangeText={setTitle}
              placeholder="Looking for a quiz team"
              placeholderTextColor={C.textSecondary}
              style={s.input}
            />
          </Field>

          <Field label="Description">
            <TextInput
              value={description}
              onChangeText={setDescription}
              placeholder="What are you after? Who should join?"
              placeholderTextColor={C.textSecondary}
              style={[s.input, { minHeight: 80, textAlignVertical: 'top' }]}
              multiline
            />
          </Field>

          <Field label="Who can join">
            <View style={s.segmentRow}>
              {VISIBILITY_OPTIONS.map((opt) => {
                const active = visibility === opt.value;
                return (
                  <TouchableOpacity
                    key={opt.value}
                    style={[s.segment, active && s.segmentActive]}
                    onPress={() => setVisibility(opt.value)}
                    activeOpacity={0.85}
                  >
                    <Text style={[s.segmentLabel, active && s.segmentLabelActive]}>
                      {opt.label}
                    </Text>
                    <Text style={[s.segmentHint, active && s.segmentHintActive]}>
                      {opt.hint}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </Field>

          <Field label="Max members">
            <TextInput
              value={maxMembers}
              onChangeText={setMaxMembers}
              placeholder="(optional) leave blank for no limit"
              placeholderTextColor={C.textSecondary}
              style={s.input}
              keyboardType="number-pad"
            />
          </Field>

          <Field label="Interests">
            <Text style={s.hint}>
              Pick what this party is about — people who share these see it first.
            </Text>
            {interestsLoading ? (
              <ActivityIndicator color={C.brandPrimary} style={{ marginTop: 8 }} />
            ) : (
              <View style={s.chipWrap}>
                {interests.map((it) => {
                  const active = selected.includes(it.id);
                  return (
                    <TouchableOpacity
                      key={it.id}
                      onPress={() => toggle(it.id)}
                      activeOpacity={0.8}
                      style={[s.chip, active && s.chipActive]}
                    >
                      <Text style={[s.chipText, active && s.chipTextActive]}>
                        {it.label}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            )}
          </Field>

          <Field label="Drinks">
            <Text style={s.hint}>
              Optional — tag the drinks this party is about. People whose taste
              matches see it first.
            </Text>
            <View style={s.chipWrap}>
              {DRINK_TYPE_OPTIONS.map((opt) => {
                const active = drinks.includes(opt.value);
                return (
                  <TouchableOpacity
                    key={opt.value}
                    onPress={() => toggleDrink(opt.value)}
                    activeOpacity={0.8}
                    style={[s.chip, active && s.chipActive]}
                  >
                    <Text style={[s.chipText, active && s.chipTextActive]}>
                      {opt.label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </Field>

          {error && <Text style={s.error}>{error}</Text>}
          {isLoading && <ActivityIndicator style={{ marginTop: 16 }} />}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <View style={s.field}>
      <Text style={s.label}>{label}</Text>
      {children}
    </View>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bgBase },
  kav: { flex: 1 },

  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: C.borderDefault,
  },
  headerTitle: { fontFamily: F.headingBold, fontSize: 17, color: C.textPrimary },
  headerBtn: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.textSecondary },
  headerCta: { color: C.brandPrimary },

  content: { padding: 20, gap: 16 },

  field: { gap: 6 },
  label: { fontFamily: F.bodySemiBold, fontSize: 12, color: C.textSecondary, letterSpacing: 0.3 },
  hint: { fontFamily: F.bodyRegular, fontSize: 12, color: C.textSecondary },
  input: {
    fontFamily: F.bodyRegular, fontSize: 15, color: C.textPrimary,
    backgroundColor: C.bgInput, borderRadius: 10,
    paddingHorizontal: 12, paddingVertical: 10,
    borderWidth: 1, borderColor: C.borderDefault,
  },
  error: { fontFamily: F.bodyBold, fontSize: 13, color: C.error, marginTop: 12 },

  segmentRow: { flexDirection: 'row', gap: 10 },
  segment: {
    flex: 1, paddingVertical: 12, paddingHorizontal: 12,
    borderRadius: 10, backgroundColor: C.bgCard,
    borderWidth: 1, borderColor: C.borderDefault,
  },
  segmentActive: { backgroundColor: C.brandPrimary, borderColor: C.brandPrimary },
  segmentLabel: { fontFamily: F.bodyBold, fontSize: 14, color: C.textPrimary },
  segmentLabelActive: { color: '#FFFFFF' },
  segmentHint: { fontFamily: F.bodyRegular, fontSize: 11, color: C.textSecondary, marginTop: 3 },
  segmentHintActive: { color: '#FFFFFF' },

  chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8 },
  chip: {
    backgroundColor: C.bgCard, borderColor: C.borderDefault, borderWidth: 1,
    paddingHorizontal: 16, paddingVertical: 9, borderRadius: 999,
  },
  chipActive: { backgroundColor: C.brandPrimary, borderColor: C.brandPrimary },
  chipText: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.textSecondary },
  chipTextActive: { color: '#FFFFFF' },

  gate: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 32, gap: 12 },
  gateEmoji: { fontSize: 44 },
  gateTitle: { fontFamily: F.headingBold, fontSize: 20, color: C.textPrimary },
  gateBody: { fontFamily: F.bodyRegular, fontSize: 14, color: C.textSecondary, textAlign: 'center', lineHeight: 21 },
  gateBtn: {
    marginTop: 8, paddingVertical: 14, paddingHorizontal: 28,
    borderRadius: 12, backgroundColor: C.brandPrimary,
  },
  gateBtnText: { fontFamily: F.bodyBold, fontSize: 15, color: '#FFFFFF' },
});
