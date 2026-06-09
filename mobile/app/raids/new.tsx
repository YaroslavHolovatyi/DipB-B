/**
 * Create-a-raid modal.
 *
 * Minimal form: title, when (date + time text inputs), optional bar_id (passed
 * from `/bars/[id]?…` via search params). On submit, POSTs /raids and navigates
 * to the new raid's detail page.
 */

import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
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

import { useCreateRaidMutation } from '../../api/raidsApi';
import type { DrinkType, RaidVisibility } from '../../api/types';
import { DRINK_TYPE_OPTIONS } from '../../lib/drinkTypes';
import { C, F } from '../../theme/styleHelpers';

const VISIBILITY_OPTIONS: { value: RaidVisibility; label: string; hint: string }[] = [
  { value: 'open', label: 'Open', hint: 'Anyone can find and join' },
  { value: 'friends_only', label: 'Friends only', hint: 'Only your friends can see it' },
];

function buildScheduledAt(dateStr: string, timeStr: string): string | null {
  // Accept YYYY-MM-DD + HH:MM. Produces an ISO string in the user's local tz.
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return null;
  if (!/^\d{2}:\d{2}$/.test(timeStr)) return null;
  const combined = new Date(`${dateStr}T${timeStr}:00`);
  if (Number.isNaN(combined.getTime())) return null;
  return combined.toISOString();
}

export default function NewRaidScreen() {
  const { barId } = useLocalSearchParams<{ barId?: string }>();
  const [createRaid, { isLoading }] = useCreateRaidMutation();

  const today = new Date();
  const isoDate = today.toISOString().slice(0, 10);

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [theme, setTheme] = useState('');
  const [date, setDate] = useState(isoDate);
  const [time, setTime] = useState('19:00');
  const [maxParticipants, setMaxParticipants] = useState('');
  const [visibility, setVisibility] = useState<RaidVisibility>('open');
  const [drinks, setDrinks] = useState<DrinkType[]>([]);
  const [error, setError] = useState<string | null>(null);

  const toggleDrink = (t: DrinkType) =>
    setDrinks((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));

  const submit = async () => {
    setError(null);
    const scheduled_at = buildScheduledAt(date, time);
    if (!title.trim()) return setError('Title is required');
    if (!scheduled_at) return setError('Date/time must be YYYY-MM-DD and HH:MM');

    let max: number | null = null;
    if (maxParticipants.trim()) {
      max = Number(maxParticipants.trim());
      if (!Number.isInteger(max) || max < 2 || max > 200) {
        return setError('Max participants must be a whole number between 2 and 200');
      }
    }

    try {
      const raid = await createRaid({
        title: title.trim(),
        description: description.trim() || null,
        theme: theme.trim() || null,
        visibility,
        max_participants: max,
        bar_id: barId ? Number(barId) : null,
        scheduled_at,
        drink_types: drinks,
      }).unwrap();
      router.replace(`/raids/${raid.id}` as never);
    } catch (e: any) {
      setError(String(e?.data?.detail ?? 'Could not create the raid'));
    }
  };

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
          <Text style={s.headerTitle}>🗡️ New Raid</Text>
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
              placeholder="Friday Pints"
              placeholderTextColor={C.textSecondary}
              style={s.input}
            />
          </Field>

          <Field label="Description">
            <TextInput
              value={description}
              onChangeText={setDescription}
              placeholder="(optional)"
              placeholderTextColor={C.textSecondary}
              style={[s.input, { minHeight: 80, textAlignVertical: 'top' }]}
              multiline
            />
          </Field>

          <Field label="Theme">
            <TextInput
              value={theme}
              onChangeText={setTheme}
              placeholder="(optional) e.g. Pub quiz night"
              placeholderTextColor={C.textSecondary}
              style={s.input}
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

          <Field label="Date  (YYYY-MM-DD)">
            <TextInput
              value={date}
              onChangeText={setDate}
              placeholder="2026-06-12"
              placeholderTextColor={C.textSecondary}
              style={s.input}
              autoCapitalize="none"
              keyboardType="numbers-and-punctuation"
            />
          </Field>

          <Field label="Time  (HH:MM)">
            <TextInput
              value={time}
              onChangeText={setTime}
              placeholder="19:00"
              placeholderTextColor={C.textSecondary}
              style={s.input}
              keyboardType="numbers-and-punctuation"
            />
          </Field>

          <Field label="Max participants">
            <TextInput
              value={maxParticipants}
              onChangeText={setMaxParticipants}
              placeholder="(optional) leave blank for no limit"
              placeholderTextColor={C.textSecondary}
              style={s.input}
              keyboardType="number-pad"
            />
          </Field>

          <Field label="Drinks">
            <Text style={s.hint}>
              Tag the vibe — people whose taste matches see your raid first.
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

          {barId && (
            <Text style={s.note}>
              Tavern attached: bar #{barId}
            </Text>
          )}
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
  note: { fontFamily: F.bodyRegular, fontSize: 13, color: C.textSecondary, marginTop: 4 },
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
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 999,
  },
  chipActive: { backgroundColor: C.brandPrimary, borderColor: C.brandPrimary },
  chipText: { fontFamily: F.bodySemiBold, fontSize: 13, color: C.textSecondary },
  chipTextActive: { color: '#FFFFFF' },
});
