/**
 * Party detail.
 *
 * Shows the party, its interest tags, and the member roster. Non-members get a
 * Join button (which surfaces "party is already full" from the server). Members
 * get Leave. The host gets Cancel (and can't leave their own party).
 */

import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useListInterestsQuery } from '../../api/referenceApi';
import {
  useGetPartyQuery,
  useJoinPartyMutation,
  useLeavePartyMutation,
  useListPartyMembersQuery,
  useUpdatePartyMutation,
} from '../../api/partiesApi';
import { useAppSelector } from '../../store';
import { drinkLabel } from '../../lib/drinkTypes';
import { C, F } from '../../theme/styleHelpers';

export default function PartyDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const partyId = Number(id);
  const myId = useAppSelector((s) => s.auth.user?.id);

  const { data: party, isLoading } = useGetPartyQuery(partyId, { skip: !partyId });
  const { data: members } = useListPartyMembersQuery(partyId, { skip: !partyId });
  const { data: catalog = [] } = useListInterestsQuery();
  const [join, { isLoading: joining }] = useJoinPartyMutation();
  const [leave, { isLoading: leaving }] = useLeavePartyMutation();
  const [updateParty, { isLoading: cancelling }] = useUpdatePartyMutation();

  const [error, setError] = useState<string | null>(null);

  if (isLoading || !party) {
    return (
      <SafeAreaView style={s.safe}>
        <ActivityIndicator style={{ marginTop: 40 }} />
      </SafeAreaView>
    );
  }

  const isHost = party.host_id === myId;
  const isMember = party.my_membership === 'joined';
  const isTerminal = party.status === 'cancelled' || party.status === 'closed';
  const labelOf = (iid: number) => catalog.find((c) => c.id === iid)?.label ?? `#${iid}`;

  const doJoin = async () => {
    setError(null);
    try {
      await join(party.id).unwrap();
    } catch (e: any) {
      setError(String(e?.data?.detail ?? 'Could not join this party'));
    }
  };
  const doLeave = async () => {
    setError(null);
    try {
      await leave(party.id).unwrap();
    } catch (e: any) {
      setError(String(e?.data?.detail ?? 'Could not leave this party'));
    }
  };
  const doCancel = async () => {
    setError(null);
    try {
      await updateParty({ id: party.id, body: { status: 'cancelled' } }).unwrap();
    } catch (e: any) {
      setError(String(e?.data?.detail ?? 'Could not cancel this party'));
    }
  };

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <ScrollView contentContainerStyle={s.content}>
        <TouchableOpacity style={s.back} onPress={() => router.back()}>
          <Text style={s.backText}>← Back</Text>
        </TouchableOpacity>

        <Text style={s.title}>{party.title}</Text>
        {party.description && <Text style={s.description}>{party.description}</Text>}

        <View style={s.infoCard}>
          <Row label="Status">{party.status}</Row>
          <Row label="Visibility">
            {party.visibility === 'friends_only' ? 'Friends only' : 'Open'}
          </Row>
          <Row label="Members">
            {party.member_count}
            {party.max_members ? ` of ${party.max_members}` : ''}
          </Row>
          {party.match_score > 0 && <Row label="Shared interests">{party.match_score}</Row>}
        </View>

        {party.interest_ids.length > 0 && (
          <View style={s.chipWrap}>
            {party.interest_ids.map((iid) => (
              <View key={iid} style={s.tag}>
                <Text style={s.tagText}>{labelOf(iid)}</Text>
              </View>
            ))}
          </View>
        )}

        {party.drink_types.length > 0 && (
          <View style={s.chipWrap}>
            {party.drink_types.map((dt) => (
              <View key={dt} style={s.tag}>
                <Text style={s.tagText}>{drinkLabel(dt)}</Text>
              </View>
            ))}
          </View>
        )}
        {party.drink_match > 0 && (
          <Text style={s.taste}>🍻 Matches your taste</Text>
        )}

        {party.status === 'cancelled' && (
          <Text style={s.banner}>This party was cancelled.</Text>
        )}
        {party.status === 'closed' && (
          <Text style={s.banner}>This party is closed.</Text>
        )}

        {isHost && party.status !== 'cancelled' && (
          <TouchableOpacity
            style={s.splitBtn}
            onPress={() =>
              router.push(`/checks/new?party_id=${party.id}` as never)
            }
            activeOpacity={0.85}
          >
            <Text style={s.splitText}>🧾 Split the shared bill</Text>
          </TouchableOpacity>
        )}

        {!isTerminal && (
          <>
            {!isHost && (
              isMember ? (
                <TouchableOpacity
                  style={[s.actionBtn, s.leaveBtn]}
                  onPress={doLeave}
                  disabled={leaving}
                  activeOpacity={0.85}
                >
                  <Text style={s.leaveText}>{leaving ? 'Leaving…' : 'Leave party'}</Text>
                </TouchableOpacity>
              ) : (
                <TouchableOpacity
                  style={[s.actionBtn, party.is_full ? s.fullBtn : s.joinBtn]}
                  onPress={doJoin}
                  disabled={joining || party.is_full}
                  activeOpacity={0.85}
                >
                  <Text style={party.is_full ? s.fullText : s.joinText}>
                    {party.is_full ? 'Party is full' : joining ? 'Joining…' : 'Join party'}
                  </Text>
                </TouchableOpacity>
              )
            )}

            {isHost && (
              <TouchableOpacity
                style={[s.actionBtn, s.cancelBtn]}
                onPress={doCancel}
                disabled={cancelling}
                activeOpacity={0.85}
              >
                <Text style={s.cancelText}>{cancelling ? 'Cancelling…' : 'Cancel party'}</Text>
              </TouchableOpacity>
            )}
          </>
        )}

        {error && <Text style={s.error}>{error}</Text>}

        <Text style={s.sectionTitle}>Members</Text>
        <View style={s.roster}>
          {(members ?? []).map((m) => (
            <View key={m.user_id} style={s.memberRow}>
              <Text style={s.memberName}>{m.first_name}</Text>
              <Text style={s.memberMeta}>
                @{m.username}
                {m.user_id === party.host_id ? ' · host' : m.status === 'invited' ? ' · invited' : ''}
              </Text>
            </View>
          ))}
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
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

  back: { paddingVertical: 8 },
  backText: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.textSecondary },

  title: { fontFamily: F.headingBold, fontSize: 24, color: C.textPrimary, marginTop: 4 },
  description: { fontFamily: F.bodyRegular, fontSize: 14, color: C.textSecondary, marginTop: 8, lineHeight: 21 },

  infoCard: {
    marginTop: 16, padding: 14,
    backgroundColor: C.bgCard, borderColor: C.borderDefault, borderWidth: 1, borderRadius: 14, gap: 8,
  },
  row: { flexDirection: 'row', justifyContent: 'space-between' },
  rowLabel: { fontFamily: F.bodyRegular, fontSize: 13, color: C.textSecondary },
  rowValue: { fontFamily: F.bodyBold, fontSize: 13, color: C.textPrimary },

  chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 14 },
  tag: {
    backgroundColor: C.bgCard, borderColor: C.borderDefault, borderWidth: 1,
    paddingHorizontal: 14, paddingVertical: 7, borderRadius: 999,
  },
  tagText: { fontFamily: F.bodySemiBold, fontSize: 13, color: C.textSecondary },
  taste: { fontFamily: F.bodySemiBold, fontSize: 13, color: C.brandPrimary, marginTop: 12 },

  banner: { fontFamily: F.bodyBold, color: C.error, textAlign: 'center', marginTop: 20 },

  actionBtn: { marginTop: 20, paddingVertical: 15, alignItems: 'center', borderRadius: 12 },
  joinBtn: { backgroundColor: C.brandPrimary },
  joinText: { fontFamily: F.bodyBold, fontSize: 15, color: '#FFFFFF' },
  fullBtn: { backgroundColor: C.bgCard, borderWidth: 1, borderColor: C.borderDefault },
  fullText: { fontFamily: F.bodyBold, fontSize: 15, color: C.textDisabled },
  leaveBtn: { backgroundColor: C.errorSubtle },
  leaveText: { fontFamily: F.bodyBold, fontSize: 15, color: C.error },
  cancelBtn: { backgroundColor: C.errorSubtle },
  cancelText: { fontFamily: F.bodyBold, fontSize: 15, color: C.error },

  splitBtn: {
    marginTop: 16, paddingVertical: 14, alignItems: 'center', borderRadius: 12,
    backgroundColor: C.accentGoldSubtle, borderWidth: 1, borderColor: C.borderDefault,
  },
  splitText: { fontFamily: F.bodyBold, fontSize: 15, color: C.textPrimary },

  error: { fontFamily: F.bodyBold, fontSize: 13, color: C.error, marginTop: 14, textAlign: 'center' },

  sectionTitle: { fontFamily: F.headingSemi, fontSize: 16, color: C.textPrimary, marginTop: 26, marginBottom: 10 },
  roster: { gap: 8 },
  memberRow: {
    padding: 12, borderRadius: 12,
    backgroundColor: C.bgCard, borderWidth: 1, borderColor: C.borderDefault,
  },
  memberName: { fontFamily: F.bodyBold, fontSize: 14, color: C.textPrimary },
  memberMeta: { fontFamily: F.bodyRegular, fontSize: 12, color: C.textSecondary, marginTop: 2 },
});
