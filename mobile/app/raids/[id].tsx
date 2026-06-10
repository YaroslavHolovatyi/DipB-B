/**
 * Raid detail + full lifecycle.
 *
 * Everyone sees: title, theme, time, status, going/maybe count, and three RSVP
 * buttons (going / maybe / decline). A double-booking attempt surfaces the
 * server's 409 inline.
 *
 * Once they're `going`, a "Check in" button moves them to `arrived` (and flips
 * the raid to `ongoing`).
 *
 * The organiser additionally gets the host console:
 *   • a verification roster — mark each attendee Attended / No-show
 *   • Complete   — wraps it up; anyone unverified is auto-marked no-show
 *   • Abort      — kills an in-progress raid; nobody is scored
 *   • Cancel     — call it off before it starts
 *
 * The screen subscribes to WS-driven cache invalidation so RSVPs/verdicts from
 * other devices appear without polling.
 */

import { Ionicons } from '@expo/vector-icons';
import { router, useLocalSearchParams } from 'expo-router';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  useAbortRaidMutation,
  useCancelRaidMutation,
  useCheckpointRaidMutation,
  useCompleteRaidMutation,
  useGetRaidQuery,
  useListRaidParticipantsQuery,
  useRsvpRaidMutation,
  useVerifyRaidMutation,
} from '../../api/raidsApi';
import type { AttendanceVerdict, RaidParticipantDetail, RsvpChoice } from '../../api/types';
import type { ComponentProps } from 'react';
import { useState } from 'react';
import { useAppSelector } from '../../store';
import { drinkLabel } from '../../lib/drinkTypes';
import { C, F } from '../../theme/styleHelpers';

type IoniconName = ComponentProps<typeof Ionicons>['name'];

const RSVP_OPTIONS: { value: RsvpChoice; label: string; icon: IoniconName }[] = [
  { value: 'going', label: 'Going', icon: 'shield-checkmark' },
  { value: 'maybe', label: 'Maybe', icon: 'help-circle' },
  { value: 'declined', label: 'Decline', icon: 'close-circle' },
];

const TERMINAL = ['completed', 'cancelled', 'aborted'] as const;

const STATUS_LABEL: Record<string, string> = {
  arrived: 'Checked in',
  attended: 'Attended',
  no_show: 'No-show',
  going: 'Going',
  maybe: 'Maybe',
  declined: 'Declined',
};

export default function RaidDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const raidId = Number(id);
  const myId = useAppSelector((s) => s.auth.user?.id);

  const { data: raid, isLoading } = useGetRaidQuery(raidId, { skip: !raidId });
  const [rsvp, { isLoading: rsvpLoading }] = useRsvpRaidMutation();
  const [cancelRaid, { isLoading: cancelLoading }] = useCancelRaidMutation();
  const [checkpoint, { isLoading: checkpointLoading }] = useCheckpointRaidMutation();
  const [completeRaid, { isLoading: completeLoading }] = useCompleteRaidMutation();
  const [abortRaid, { isLoading: abortLoading }] = useAbortRaidMutation();

  const [error, setError] = useState<string | null>(null);

  const isOrganizer = !!raid && raid.organizer_id === myId;
  const isTerminal = !!raid && (TERMINAL as readonly string[]).includes(raid.status);

  const { data: participants } = useListRaidParticipantsQuery(raidId, {
    skip: !raidId || !isOrganizer,
  });

  if (isLoading || !raid) {
    return (
      <SafeAreaView style={s.safe}>
        <ActivityIndicator style={{ marginTop: 40 }} />
      </SafeAreaView>
    );
  }

  const when = new Date(raid.scheduled_at);
  const checkedIn = raid.my_rsvp === 'arrived' || raid.my_rsvp === 'attended';

  const doRsvp = async (status: RsvpChoice) => {
    setError(null);
    try {
      await rsvp({ id: raid.id, status }).unwrap();
    } catch (e: any) {
      setError(String(e?.data?.detail ?? 'Could not update your response'));
    }
  };

  const doCheckpoint = async () => {
    setError(null);
    try {
      await checkpoint(raid.id).unwrap();
    } catch (e: any) {
      setError(String(e?.data?.detail ?? 'Could not check you in'));
    }
  };

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <ScrollView contentContainerStyle={s.content}>
        <TouchableOpacity style={s.back} onPress={() => router.back()}>
          <Ionicons name="chevron-back" size={18} color={C.textSecondary} />
          <Text style={s.backText}>Back</Text>
        </TouchableOpacity>

        <Text style={s.title}>{raid.title}</Text>
        {raid.theme ? (
          <View style={s.themeRow}>
            <Ionicons name="dice" size={14} color={C.accentGoldText} />
            <Text style={s.theme}>{raid.theme}</Text>
          </View>
        ) : null}
        {raid.description && <Text style={s.description}>{raid.description}</Text>}

        <View style={s.infoCard}>
          <Row label="When">{when.toLocaleString()}</Row>
          <Row label="Status">{raid.status}</Row>
          <Row label="Visibility">
            {raid.visibility === 'friends_only' ? 'Friends only' : 'Open'}
          </Row>
          <Row label="Going / Maybe">
            {raid.participant_count}
            {raid.max_participants ? ` of ${raid.max_participants}` : ''}
          </Row>
          {raid.bar_id && <Row label="Tavern">#{raid.bar_id}</Row>}
        </View>

        {raid.drink_types.length > 0 && (
          <View style={s.chipWrap}>
            {raid.drink_types.map((dt) => (
              <View key={dt} style={s.tag}>
                <Text style={s.tagText}>{drinkLabel(dt)}</Text>
              </View>
            ))}
          </View>
        )}
        {raid.drink_match > 0 && (
          <View style={s.tasteRow}>
            <Ionicons name="beer" size={13} color={C.accentGoldText} />
            <Text style={s.taste}>Matches your taste</Text>
          </View>
        )}

        {raid.status === 'cancelled' && (
          <Text style={s.banner}>This raid was cancelled.</Text>
        )}
        {raid.status === 'aborted' && (
          <Text style={s.banner}>This raid was called off.</Text>
        )}
        {raid.status === 'completed' && (
          <Text style={[s.banner, s.bannerOk]}>This raid is complete.</Text>
        )}
        {raid.status === 'completed' && isOrganizer && (
          <TouchableOpacity
            style={s.splitBtn}
            onPress={() =>
              router.push(`/checks/new?raid_id=${raid.id}` as never)
            }
            activeOpacity={0.85}
          >
            <Ionicons name="receipt-outline" size={16} color={C.textPrimary} />
            <Text style={s.splitText}>Split the shared bill</Text>
          </TouchableOpacity>
        )}

        {!isTerminal && (
          <>
            <Text style={s.sectionTitle}>Your response</Text>
            <View style={s.rsvpRow}>
              {RSVP_OPTIONS.map((opt) => {
                const active = raid.my_rsvp === opt.value;
                return (
                  <TouchableOpacity
                    key={opt.value}
                    style={[s.rsvpBtn, active && s.rsvpBtnActive]}
                    onPress={() => doRsvp(opt.value)}
                    disabled={rsvpLoading}
                    activeOpacity={0.85}
                  >
                    <Ionicons
                      name={opt.icon}
                      size={20}
                      color={active ? '#FFFFFF' : C.textSecondary}
                    />
                    <Text style={[s.rsvpLabel, active && s.rsvpLabelActive]}>
                      {opt.label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>

            {/* Check-in: visible once you've committed as going */}
            {(raid.my_rsvp === 'going' || checkedIn) && (
              <TouchableOpacity
                style={[s.checkinBtn, checkedIn && s.checkinDone]}
                onPress={doCheckpoint}
                disabled={checkpointLoading || checkedIn}
                activeOpacity={0.85}
              >
                <View style={s.checkinInner}>
                  {checkedIn && (
                    <Ionicons name="checkmark" size={16} color="#34D399" />
                  )}
                  <Text style={[s.checkinText, checkedIn && s.checkinDoneText]}>
                    {checkedIn ? 'Checked in' : checkpointLoading ? 'Checking in…' : 'Check in on-site'}
                  </Text>
                </View>
              </TouchableOpacity>
            )}

            {error && <Text style={s.error}>{error}</Text>}

            {isOrganizer && (
              <HostConsole
                raidId={raid.id}
                organizerId={raid.organizer_id}
                participants={participants ?? []}
              />
            )}

            {isOrganizer && (
              <View style={s.hostActions}>
                {raid.status === 'planned' && (
                  <TouchableOpacity
                    style={[s.hostBtn, s.cancelBtn]}
                    onPress={() => cancelRaid(raid.id)}
                    disabled={cancelLoading}
                    activeOpacity={0.85}
                  >
                    <Text style={s.cancelText}>
                      {cancelLoading ? 'Cancelling…' : 'Cancel raid'}
                    </Text>
                  </TouchableOpacity>
                )}
                <TouchableOpacity
                  style={[s.hostBtn, s.completeBtn]}
                  onPress={() => completeRaid(raid.id)}
                  disabled={completeLoading}
                  activeOpacity={0.85}
                >
                  <Text style={s.completeText}>
                    {completeLoading ? 'Completing…' : 'Complete raid'}
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[s.hostBtn, s.abortBtn]}
                  onPress={() => abortRaid(raid.id)}
                  disabled={abortLoading}
                  activeOpacity={0.85}
                >
                  <Text style={s.abortText}>
                    {abortLoading ? 'Aborting…' : 'Abort raid'}
                  </Text>
                </TouchableOpacity>
              </View>
            )}
          </>
        )}

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

/** Organiser-only roster: mark each participant Attended / No-show. */
function HostConsole({
  raidId,
  organizerId,
  participants,
}: {
  raidId: number;
  organizerId: number;
  participants: RaidParticipantDetail[];
}) {
  const [verify, { isLoading }] = useVerifyRaidMutation();
  const [pending, setPending] = useState<number | null>(null);

  const roster = participants.filter((p) => p.user_id !== organizerId);
  if (roster.length === 0) {
    return (
      <>
        <Text style={s.sectionTitle}>Attendance</Text>
        <Text style={s.hint}>No one else has joined yet.</Text>
      </>
    );
  }

  const mark = async (userId: number, verdict: AttendanceVerdict) => {
    setPending(userId);
    try {
      await verify({ id: raidId, marks: [{ user_id: userId, verdict }] }).unwrap();
    } catch {
      // swallow — roster refetch keeps the source of truth
    } finally {
      setPending(null);
    }
  };

  return (
    <>
      <Text style={s.sectionTitle}>Attendance</Text>
      <Text style={s.hint}>
        Confirm who showed up. This feeds each person&apos;s social rating.
      </Text>
      <View style={s.roster}>
        {roster.map((p) => {
          const verified = p.verified_at != null;
          const busy = isLoading && pending === p.user_id;
          return (
            <View key={p.user_id} style={s.rosterRow}>
              <View style={{ flex: 1 }}>
                <Text style={s.rosterName}>{p.first_name}</Text>
                <Text style={s.rosterMeta}>
                  @{p.username} · {STATUS_LABEL[p.status] ?? p.status}
                </Text>
              </View>
              {verified ? (
                <Text
                  style={[
                    s.verdictBadge,
                    p.status === 'attended' ? s.verdictOk : s.verdictBad,
                  ]}
                >
                  {p.status === 'attended' ? 'Attended' : 'No-show'}
                </Text>
              ) : (
                <View style={s.verdictBtns}>
                  <TouchableOpacity
                    style={[s.verdictBtn, s.verdictBtnOk]}
                    onPress={() => mark(p.user_id, 'attended')}
                    disabled={busy}
                    activeOpacity={0.8}
                  >
                    <Text style={s.verdictBtnOkText}>{busy ? '…' : 'Here'}</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[s.verdictBtn, s.verdictBtnBad]}
                    onPress={() => mark(p.user_id, 'no_show')}
                    disabled={busy}
                    activeOpacity={0.8}
                  >
                    <Text style={s.verdictBtnBadText}>No-show</Text>
                  </TouchableOpacity>
                </View>
              )}
            </View>
          );
        })}
      </View>
    </>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <View style={s.row}>
      <Text style={s.rowLabel}>{label}</Text>
      <Text style={s.rowValue}>{children}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bgBase },
  content: { paddingHorizontal: 20, paddingTop: 8, paddingBottom: 40 },

  back: { flexDirection: 'row', alignItems: 'center', gap: 2, paddingVertical: 8 },
  backText: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.textSecondary },

  title: { fontFamily: F.headingBold, fontSize: 24, color: C.textPrimary, marginTop: 4 },
  themeRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 6 },
  theme: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.brandPrimary },
  description: { fontFamily: F.bodyRegular, fontSize: 14, color: C.textSecondary, marginTop: 8, lineHeight: 21 },

  chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 14 },
  tag: {
    backgroundColor: C.bgCard, borderColor: C.borderDefault, borderWidth: 1,
    paddingHorizontal: 14, paddingVertical: 7, borderRadius: 999,
  },
  tagText: { fontFamily: F.bodySemiBold, fontSize: 13, color: C.textSecondary },
  tasteRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 12 },
  taste: { fontFamily: F.bodySemiBold, fontSize: 13, color: C.brandPrimary },

  infoCard: {
    marginTop: 16, padding: 14,
    backgroundColor: C.bgCard, borderColor: C.borderDefault, borderWidth: 1, borderRadius: 14,
    gap: 8,
  },
  row: { flexDirection: 'row', justifyContent: 'space-between' },
  rowLabel: { fontFamily: F.bodyRegular, fontSize: 13, color: C.textSecondary },
  rowValue: { fontFamily: F.bodyBold, fontSize: 13, color: C.textPrimary },

  banner: {
    fontFamily: F.bodyBold, color: C.error,
    textAlign: 'center', marginTop: 20,
  },
  bannerOk: { color: C.brandPrimary },

  sectionTitle: {
    fontFamily: F.headingSemi, fontSize: 16, color: C.textPrimary,
    marginTop: 24, marginBottom: 10,
  },
  hint: { fontFamily: F.bodyRegular, fontSize: 12, color: C.textSecondary, marginBottom: 10 },

  rsvpRow: { flexDirection: 'row', gap: 10 },
  rsvpBtn: {
    flex: 1, alignItems: 'center', gap: 4, paddingVertical: 14,
    borderRadius: 12, backgroundColor: C.bgCard,
    borderWidth: 1, borderColor: C.borderDefault,
  },
  rsvpBtnActive: { backgroundColor: C.brandPrimary, borderColor: C.brandPrimary },
  rsvpLabel: { fontFamily: F.bodyBold, fontSize: 13, color: C.textPrimary },
  rsvpLabelActive: { color: '#FFFFFF' },

  checkinBtn: {
    marginTop: 14, paddingVertical: 14, alignItems: 'center',
    borderRadius: 12, backgroundColor: C.brandPrimary,
  },
  checkinDone: { backgroundColor: C.bgCard, borderWidth: 1, borderColor: C.borderDefault },
  checkinInner: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  checkinText: { fontFamily: F.bodyBold, fontSize: 14, color: '#FFFFFF' },
  checkinDoneText: { color: C.textSecondary },

  error: { fontFamily: F.bodyBold, fontSize: 13, color: C.error, marginTop: 14, textAlign: 'center' },

  // Host roster
  roster: { gap: 8 },
  rosterRow: {
    flexDirection: 'row', alignItems: 'center',
    padding: 12, borderRadius: 12,
    backgroundColor: C.bgCard, borderWidth: 1, borderColor: C.borderDefault,
  },
  rosterName: { fontFamily: F.bodyBold, fontSize: 14, color: C.textPrimary },
  rosterMeta: { fontFamily: F.bodyRegular, fontSize: 12, color: C.textSecondary, marginTop: 2 },
  verdictBtns: { flexDirection: 'row', gap: 8 },
  verdictBtn: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 9 },
  verdictBtnOk: { backgroundColor: C.brandPrimary },
  verdictBtnOkText: { fontFamily: F.bodyBold, fontSize: 12, color: '#FFFFFF' },
  verdictBtnBad: { backgroundColor: C.errorSubtle },
  verdictBtnBadText: { fontFamily: F.bodyBold, fontSize: 12, color: C.error },
  verdictBadge: { fontFamily: F.bodyBold, fontSize: 12, paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8, overflow: 'hidden' },
  verdictOk: { color: '#FFFFFF', backgroundColor: C.brandPrimary },
  verdictBad: { color: C.error, backgroundColor: C.errorSubtle },

  // Host actions
  hostActions: { marginTop: 24, gap: 10 },
  hostBtn: { paddingVertical: 14, alignItems: 'center', borderRadius: 12 },
  completeBtn: { backgroundColor: C.brandPrimary },
  completeText: { fontFamily: F.bodyBold, fontSize: 14, color: '#FFFFFF' },
  abortBtn: { backgroundColor: C.errorSubtle },
  abortText: { fontFamily: F.bodyBold, fontSize: 14, color: C.error },
  cancelBtn: { backgroundColor: C.bgCard, borderWidth: 1, borderColor: C.borderDefault },
  cancelText: { fontFamily: F.bodyBold, fontSize: 14, color: C.textSecondary },

  splitBtn: {
    marginTop: 14, paddingVertical: 14, flexDirection: 'row',
    alignItems: 'center', justifyContent: 'center', gap: 8, borderRadius: 12,
    backgroundColor: C.accentGoldSubtle, borderWidth: 1, borderColor: C.borderDefault,
  },
  splitText: { fontFamily: F.bodyBold, fontSize: 14, color: C.textPrimary },
});
