/**
 * Race Quiz — the onboarding step that assigns a D&D race.
 *
 * Flow:
 *   1. GET /quiz/questions  → one question shown at a time with a progress bar.
 *   2. The user picks exactly one answer per question.
 *   3. On the last question, POST /quiz/submit with the flat list of answer ids
 *      (in question order). The backend tallies the per-race scores and returns
 *      the winning race.
 *   4. We refetch /auth/me so `race_id` lands in the Redux user, then show a
 *      result card. "Enter the Tavern" routes into the app.
 *
 * Reachable two ways:
 *   - Onboarding: the root layout force-redirects here whenever an authenticated
 *     user still has `race_id == null` (see app/_layout.tsx).
 *   - Retake: from Profile → "Retake race quiz". In that case the user already
 *     has a race, so on finish we just `router.back()` instead of replacing.
 */

import { Ionicons } from '@expo/vector-icons';
import { router, Stack, useLocalSearchParams } from 'expo-router';
import { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { raceImage } from '../../assets';
import { useLazyMeQuery } from '../../api/authApi';
import { useListQuestionsQuery, useSubmitQuizMutation } from '../../api/quizApi';
import { useLazyGetRaceQuery } from '../../api/referenceApi';
import type { QuizResult, Race } from '../../api/types';
import { useAppDispatch } from '../../store';
import { userUpdated } from '../../store/authSlice';
import { C, F } from '../../theme/styleHelpers';

type Gender = 'm' | 'f';

export default function QuizScreen() {
  const dispatch = useAppDispatch();
  const params = useLocalSearchParams<{ retake?: string }>();
  const isRetake = params.retake === '1';

  const { data: questions = [], isLoading, isError, refetch } = useListQuestionsQuery();
  const [submitQuiz, { isLoading: submitting }] = useSubmitQuizMutation();
  const [fetchMe] = useLazyMeQuery();
  const [fetchRace] = useLazyGetRaceQuery();

  const [step, setStep] = useState(0);
  const [picks, setPicks] = useState<Record<number, number>>({}); // questionId -> answerId
  const [gender, setGender] = useState<Gender | null>(null);
  const [result, setResult] = useState<QuizResult | null>(null);
  const [resultRace, setResultRace] = useState<Race | null>(null);
  const [error, setError] = useState<string | null>(null);

  const ordered = useMemo(
    () => [...questions].sort((a, b) => a.position - b.position),
    [questions],
  );
  const total = ordered.length;
  // A gender step is appended after the questions, so there are total + 1 steps.
  const totalSteps = total + 1;
  const onGenderStep = step === total;
  const current = onGenderStep ? undefined : ordered[step];
  const answeredCount = Object.keys(picks).length + (gender ? 1 : 0);
  const isLast = step === total; // the gender step is the final one
  const currentPicked = onGenderStep
    ? gender != null
    : current
      ? picks[current.id] != null
      : false;

  const pick = (answerId: number) => {
    if (!current) return;
    setPicks((p) => ({ ...p, [current.id]: answerId }));
  };

  const goNext = () => {
    if (!isLast) {
      setStep((s) => Math.min(s + 1, total));
    } else {
      void finish();
    }
  };

  const finish = async () => {
    setError(null);
    // Flat list of answer ids, in question order.
    const answerIds = ordered.map((q) => picks[q.id]).filter((id): id is number => id != null);
    if (answerIds.length !== total) {
      setError('Please answer every question before finishing.');
      return;
    }
    if (!gender) {
      setError('Please choose your character before finishing.');
      return;
    }
    try {
      const res = await submitQuiz({ answer_ids: answerIds, gender }).unwrap();
      setResult(res);
      // Pull the race row for color + description in the result card.
      try {
        const race = await fetchRace(res.race_id).unwrap();
        setResultRace(race);
      } catch {
        /* non-fatal — we still have the race name from the result */
      }
      // Refresh the Redux user so race_id is set everywhere.
      try {
        const me = await fetchMe().unwrap();
        dispatch(userUpdated(me));
      } catch {
        /* the auth tag was invalidated; a later screen will refetch */
      }
    } catch (e: any) {
      const detail = e?.data?.detail ?? 'Could not submit the quiz. Please try again.';
      setError(String(detail));
    }
  };

  const leave = () => {
    if (isRetake) router.back();
    else router.replace('/(tabs)' as never);
  };

  // ─── Result card ──────────────────────────────────────────────────────────
  if (result) {
    const accent = resultRace?.primary_color ?? C.brandPrimary;
    const avatar = raceImage(result.race_slug, result.gender ?? gender);
    return (
      <SafeAreaView style={s.safe} edges={['top', 'bottom']}>
        <Stack.Screen options={{ headerShown: false }} />
        <View style={s.resultWrap}>
          <Text style={s.resultKicker}>The dice have spoken…</Text>
          {avatar && (
            <Image
              source={avatar}
              style={[s.resultAvatar, { borderColor: accent }]}
              resizeMode="cover"
            />
          )}
          <View style={[s.resultBadge, { borderColor: accent, backgroundColor: accent + '18' }]}>
            <Text style={[s.resultRace, { color: accent }]}>{result.race_name}</Text>
          </View>
          {resultRace?.title && <Text style={s.resultTitle}>{resultRace.title}</Text>}
          {resultRace?.description && (
            <Text style={s.resultDesc}>{resultRace.description}</Text>
          )}
          <TouchableOpacity
            style={[s.primary, { backgroundColor: accent }]}
            activeOpacity={0.85}
            onPress={leave}
          >
            <Text style={s.primaryText}>
              {isRetake ? 'Back to Profile' : 'Enter the Tavern'}
            </Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // ─── Loading / error / empty ───────────────────────────────────────────────
  if (isLoading) {
    return (
      <SafeAreaView style={s.safe}>
        <Stack.Screen options={{ headerShown: false }} />
        <View style={s.center}>
          <ActivityIndicator color={C.brandPrimary} />
          <Text style={s.muted}>Rolling the questions…</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (isError || total === 0) {
    return (
      <SafeAreaView style={s.safe}>
        <Stack.Screen options={{ headerShown: false }} />
        <View style={s.center}>
          <Ionicons name="dice-outline" size={48} color={C.brandPrimary} />
          <Text style={s.errTitle}>The quiz scroll is blank</Text>
          <Text style={s.muted}>
            {isError
              ? 'Could not reach the backend. Make sure it is running and seeded.'
              : 'No quiz questions are seeded yet.'}
          </Text>
          <TouchableOpacity style={s.secondary} onPress={() => refetch()} activeOpacity={0.85}>
            <Text style={s.secondaryText}>Try again</Text>
          </TouchableOpacity>
          {isRetake && (
            <TouchableOpacity onPress={() => router.back()} activeOpacity={0.7}>
              <Text style={s.skipText}>Go back</Text>
            </TouchableOpacity>
          )}
        </View>
      </SafeAreaView>
    );
  }

  // ─── Question stepper ──────────────────────────────────────────────────────
  const progress = totalSteps > 0 ? answeredCount / totalSteps : 0;
  return (
    <SafeAreaView style={s.safe} edges={['top', 'bottom']}>
      <Stack.Screen options={{ headerShown: false }} />

      <View style={s.header}>
        <View style={s.headerTop}>
          <View style={s.kickerRow}>
            <Ionicons name="sparkles" size={16} color={C.brandPrimary} />
            <Text style={s.kicker}>{onGenderStep ? 'One last thing' : 'Discover Your Race'}</Text>
          </View>
          <Text style={s.counter}>
            {step + 1} / {totalSteps}
          </Text>
        </View>
        <View style={s.progressTrack}>
          <View style={[s.progressFill, { width: `${Math.round(progress * 100)}%` }]} />
        </View>
      </View>

      <ScrollView
        contentContainerStyle={s.body}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {onGenderStep ? (
          <>
            <Text style={s.question}>How should your hero be depicted?</Text>
            <View style={s.answers}>
              {(
                [
                  { value: 'm' as Gender, label: 'Male', icon: 'man' as const },
                  { value: 'f' as Gender, label: 'Female', icon: 'woman' as const },
                ]
              ).map((opt) => {
                const active = gender === opt.value;
                return (
                  <TouchableOpacity
                    key={opt.value}
                    style={[s.answer, active && s.answerActive]}
                    activeOpacity={0.85}
                    onPress={() => setGender(opt.value)}
                  >
                    <Ionicons
                      name={opt.icon}
                      size={22}
                      color={active ? C.brandPrimary : C.textSecondary}
                    />
                    <Text style={[s.answerText, active && s.answerTextActive]}>{opt.label}</Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </>
        ) : (
          <>
            <Text style={s.question}>{current?.text}</Text>

            <View style={s.answers}>
              {current?.answers
                .slice()
                .sort((a, b) => a.position - b.position)
                .map((ans) => {
                  const active = picks[current.id] === ans.id;
                  return (
                    <TouchableOpacity
                      key={ans.id}
                      style={[s.answer, active && s.answerActive]}
                      activeOpacity={0.85}
                      onPress={() => pick(ans.id)}
                    >
                      <View style={[s.radio, active && s.radioActive]}>
                        {active && <View style={s.radioDot} />}
                      </View>
                      <Text style={[s.answerText, active && s.answerTextActive]}>{ans.text}</Text>
                    </TouchableOpacity>
                  );
                })}
            </View>
          </>
        )}

        {error && <Text style={s.errorText}>{error}</Text>}
      </ScrollView>

      <View style={s.footer}>
        {step > 0 && (
          <TouchableOpacity
            style={s.backBtn}
            activeOpacity={0.8}
            onPress={() => setStep((sv) => Math.max(0, sv - 1))}
          >
            <Text style={s.backBtnText}>Back</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity
          style={[s.primary, (!currentPicked || submitting) && s.primaryDisabled, { flex: 1 }]}
          activeOpacity={0.85}
          disabled={!currentPicked || submitting}
          onPress={goNext}
        >
          {submitting ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={s.primaryText}>{isLast ? 'Reveal my race' : 'Next'}</Text>
          )}
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bgBase },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12, padding: 24 },
  emoji: { fontSize: 44 },
  muted: { fontFamily: F.bodyRegular, fontSize: 14, color: C.textSecondary, textAlign: 'center' },
  errTitle: { fontFamily: F.headingBold, fontSize: 20, color: C.textPrimary, textAlign: 'center' },

  header: { paddingHorizontal: 20, paddingTop: 8, paddingBottom: 12, gap: 10 },
  headerTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  kickerRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  kicker: { fontFamily: F.bodyBold, fontSize: 14, color: C.brandPrimary },
  counter: { fontFamily: F.monoMedium, fontSize: 13, color: C.textSecondary },
  progressTrack: { height: 6, borderRadius: 3, backgroundColor: C.bgInput, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 3, backgroundColor: C.brandPrimary },

  body: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 24 },
  question: {
    fontFamily: F.headingBold, fontSize: 24, color: C.textPrimary,
    lineHeight: 32, marginBottom: 20,
  },

  answers: { gap: 12 },
  answer: {
    flexDirection: 'row', alignItems: 'center', gap: 14,
    backgroundColor: C.bgCard, borderWidth: 1.5, borderColor: C.borderDefault,
    borderRadius: 14, paddingVertical: 16, paddingHorizontal: 16,
  },
  answerActive: { borderColor: C.brandPrimary, backgroundColor: C.brandPrimarySubtle },
  radio: {
    width: 22, height: 22, borderRadius: 11, borderWidth: 2,
    borderColor: C.borderStrong, alignItems: 'center', justifyContent: 'center',
  },
  radioActive: { borderColor: C.brandPrimary },
  radioDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: C.brandPrimary },
  answerText: { flex: 1, fontFamily: F.bodySemiBold, fontSize: 15, color: C.textPrimary },
  answerTextActive: { color: C.brandPrimaryHover },

  errorText: {
    fontFamily: F.bodySemiBold, fontSize: 13, color: C.error,
    marginTop: 16, textAlign: 'center',
  },

  footer: {
    flexDirection: 'row', gap: 12, paddingHorizontal: 20, paddingTop: 12, paddingBottom: 8,
    borderTopWidth: 1, borderTopColor: C.borderDefault,
  },
  backBtn: {
    paddingHorizontal: 20, borderRadius: 14, alignItems: 'center', justifyContent: 'center',
    borderWidth: 1.5, borderColor: C.borderDefault, backgroundColor: C.bgCard,
  },
  backBtnText: { fontFamily: F.bodyBold, fontSize: 15, color: C.textSecondary },

  primary: {
    borderRadius: 14, paddingVertical: 16, alignItems: 'center', justifyContent: 'center',
    backgroundColor: C.brandPrimary,
  },
  primaryDisabled: { opacity: 0.45 },
  primaryText: { fontFamily: F.bodyBold, fontSize: 16, color: '#FFFFFF' },

  secondary: {
    marginTop: 8, borderRadius: 12, paddingVertical: 12, paddingHorizontal: 24,
    backgroundColor: C.bgInput,
  },
  secondaryText: { fontFamily: F.bodyBold, fontSize: 14, color: C.textPrimary },
  skipText: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.textSecondary, marginTop: 12 },

  // Result
  resultWrap: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 28, gap: 16 },
  resultKicker: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.textSecondary },
  resultAvatar: { width: 160, height: 160, borderRadius: 80, borderWidth: 3 },
  resultBadge: {
    paddingHorizontal: 28, paddingVertical: 16, borderRadius: 999, borderWidth: 2,
  },
  resultRace: { fontFamily: F.headingBold, fontSize: 32, letterSpacing: 0.5 },
  resultTitle: { fontFamily: F.headingSemi, fontSize: 18, color: C.textPrimary, textAlign: 'center' },
  resultDesc: {
    fontFamily: F.bodyRegular, fontSize: 15, color: C.textSecondary,
    textAlign: 'center', lineHeight: 22, marginBottom: 8,
  },
});
