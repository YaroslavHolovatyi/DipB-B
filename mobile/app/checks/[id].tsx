/**
 * Collaborative split-room.
 *
 * Lists every line item; you tap to claim a quantity. Real-time updates flow
 * through the WS `assignment.updated` event, which the bridge translates into
 * a `Check` tag invalidation — RTK Query then refetches this screen.
 *
 * Bottom action bar handles Ready / Unready and the D20 dice proposal.
 */

import { router, useLocalSearchParams } from 'expo-router';
import { useCallback, useMemo, useState } from 'react';
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
  useGetCheckQuery,
  useJoinMutation,
  useProposeDiceMutation,
  useSetReadyMutation,
  useUpsertAssignmentMutation,
  useVoteDiceMutation,
} from '../../api/checksApi';
import type { CheckItem, CheckParticipant } from '../../api/types';
import { useAppSelector } from '../../store';
import { C, F } from '../../theme/styleHelpers';

export default function SplitRoomScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const checkId = Number(id);
  const myId = useAppSelector((s) => s.auth.user?.id);

  const { data: check, isLoading } = useGetCheckQuery(checkId, { skip: !checkId });
  const [joinRoom, { isLoading: joinLoading }] = useJoinMutation();
  const [upsertAssignment] = useUpsertAssignmentMutation();
  const [setReady] = useSetReadyMutation();
  const [proposeDice, { isLoading: proposing }] = useProposeDiceMutation();
  const [voteDice] = useVoteDiceMutation();

  const me = useMemo(
    () => check?.participants.find((p) => p.user_id === myId),
    [check, myId],
  );

  const handleClaim = useCallback(
    async (item: CheckItem, qty: number) => {
      if (!me) return;
      await upsertAssignment({
        check_id: checkId,
        item_id: item.id,
        body: { participant_id: me.id, quantity: qty },
      });
    },
    [checkId, me, upsertAssignment],
  );

  if (isLoading || !check) {
    return (
      <SafeAreaView style={s.safe}>
        <ActivityIndicator style={{ marginTop: 40 }} />
      </SafeAreaView>
    );
  }

  // If we're invited but haven't joined yet, show a "Join" prompt.
  if (me && me.status === 'invited') {
    return (
      <SafeAreaView style={s.safe} edges={['top']}>
        <View style={s.joinPrompt}>
          <Text style={s.joinTitle}>You're invited to split this receipt</Text>
          <Text style={s.joinSub}>
            Total: {Number(check.total_amount).toFixed(2)} {check.currency}
          </Text>
          <TouchableOpacity
            style={s.joinBtn}
            onPress={() => joinRoom(checkId)}
            disabled={joinLoading}
            activeOpacity={0.85}
          >
            <Text style={s.joinBtnText}>
              {joinLoading ? 'Joining…' : 'Join the room'}
            </Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const allReady = check.participants
    .filter((p) => p.status === 'joined' || p.status === 'ready')
    .every((p) => p.status === 'ready');

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={s.back}>← Back</Text>
        </TouchableOpacity>
        <Text style={s.title}>🧾 Split Room</Text>
        <View style={{ width: 50 }} />
      </View>

      <ScrollView contentContainerStyle={s.content}>
        <View style={s.totalCard}>
          <Text style={s.totalLabel}>Total</Text>
          <Text style={s.totalValue}>
            {Number(check.total_amount).toFixed(2)} {check.currency}
          </Text>
          {me && (
            <Text style={s.totalMine}>
              Your share: {Number(me.subtotal).toFixed(2)} {check.currency}
            </Text>
          )}
        </View>

        <Text style={s.sectionTitle}>Participants</Text>
        <View style={s.participantsRow}>
          {check.participants.map((p) => (
            <ParticipantChip key={p.id} p={p} isMe={p.user_id === myId} />
          ))}
        </View>

        <Text style={s.sectionTitle}>Items</Text>
        {check.items.map((item) => (
          <ItemRow
            key={item.id}
            item={item}
            myParticipantId={me?.id}
            participants={check.participants}
            onClaim={(qty) => handleClaim(item, qty)}
          />
        ))}

        <View style={{ height: 100 }} />
      </ScrollView>

      {me && (
        <View style={s.actionBar}>
          <TouchableOpacity
            style={[s.readyBtn, me.status === 'ready' && s.readyBtnDone]}
            onPress={() =>
              setReady({ id: checkId, ready: me.status !== 'ready' })
            }
          >
            <Text style={s.readyBtnText}>
              {me.status === 'ready' ? '✓ Ready' : 'Mark ready'}
            </Text>
          </TouchableOpacity>

          {allReady && (
            <TouchableOpacity
              style={s.diceBtn}
              onPress={() => proposeDice(checkId)}
              disabled={proposing}
            >
              <Text style={s.diceBtnText}>🎲 Roll D20</Text>
            </TouchableOpacity>
          )}
        </View>
      )}
    </SafeAreaView>
  );
}

// ── Sub-components ──────────────────────────────────────────────────────────
function ParticipantChip({ p, isMe }: { p: CheckParticipant; isMe: boolean }) {
  const tone =
    p.status === 'ready' ? '#10B981' : p.status === 'left' ? '#94A3B8' : C.brandPrimary;
  return (
    <View style={[chip.box, isMe && chip.boxMine, { borderColor: tone }]}>
      <Text style={[chip.name, { color: tone }]} numberOfLines={1}>
        {p.display_name}
      </Text>
      <Text style={chip.status}>{p.status}</Text>
    </View>
  );
}

function ItemRow({
  item,
  myParticipantId,
  participants,
  onClaim,
}: {
  item: CheckItem;
  myParticipantId: number | undefined;
  participants: CheckParticipant[];
  onClaim: (qty: number) => Promise<void> | void;
}) {
  const [busy, setBusy] = useState(false);
  const claimable = Number(item.quantity) - Number(item.assigned_quantity);

  return (
    <View style={s.item}>
      <View style={{ flex: 1 }}>
        <Text style={s.itemName}>{item.name}</Text>
        <Text style={s.itemMeta}>
          {Number(item.quantity)} × {Number(item.unit_price).toFixed(2)} ={' '}
          {Number(item.total_price).toFixed(2)}
        </Text>
        <Text style={s.itemMeta}>
          Assigned: {Number(item.assigned_quantity)} / {Number(item.quantity)}
        </Text>
      </View>
      <TouchableOpacity
        style={[s.claimBtn, (busy || claimable <= 0 || !myParticipantId) && s.claimBtnOff]}
        disabled={busy || claimable <= 0 || !myParticipantId}
        onPress={async () => {
          if (!myParticipantId) return;
          setBusy(true);
          try {
            await onClaim(1);
          } finally {
            setBusy(false);
          }
        }}
      >
        <Text style={s.claimBtnText}>+1</Text>
      </TouchableOpacity>
    </View>
  );
}

const chip = StyleSheet.create({
  box: {
    paddingHorizontal: 10, paddingVertical: 6,
    backgroundColor: C.bgCard, borderRadius: 999,
    borderWidth: 1.5, alignItems: 'center', minWidth: 90,
  },
  boxMine: { backgroundColor: C.brandPrimarySubtle },
  name: { fontFamily: F.bodyBold, fontSize: 12 },
  status: { fontFamily: F.bodyRegular, fontSize: 10, color: C.textSecondary },
});

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bgBase },

  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: C.borderDefault,
  },
  back: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.textSecondary, width: 60 },
  title: { fontFamily: F.headingBold, fontSize: 17, color: C.textPrimary, flex: 1, textAlign: 'center' },

  content: { padding: 20, gap: 12 },

  totalCard: {
    padding: 16, backgroundColor: C.brandPrimarySubtle, borderRadius: 14, alignItems: 'center',
  },
  totalLabel: { fontFamily: F.bodyRegular, fontSize: 13, color: C.brandPrimaryHover, letterSpacing: 0.3 },
  totalValue: { fontFamily: F.headingBold, fontSize: 30, color: C.brandPrimaryHover, marginTop: 4 },
  totalMine: { fontFamily: F.bodyBold, fontSize: 14, color: C.brandPrimaryHover, marginTop: 6 },

  sectionTitle: {
    fontFamily: F.headingSemi, fontSize: 15, color: C.textPrimary,
    marginTop: 12, marginBottom: 4,
  },
  participantsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },

  item: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    padding: 12, backgroundColor: C.bgCard,
    borderColor: C.borderDefault, borderWidth: 1, borderRadius: 12,
  },
  itemName: { fontFamily: F.bodyBold, fontSize: 14, color: C.textPrimary },
  itemMeta: { fontFamily: F.bodyRegular, fontSize: 12, color: C.textSecondary, marginTop: 2 },
  claimBtn: {
    backgroundColor: C.brandPrimary, paddingHorizontal: 12, paddingVertical: 10,
    borderRadius: 999, minWidth: 44, alignItems: 'center',
  },
  claimBtnOff: { backgroundColor: C.bgInput },
  claimBtnText: { fontFamily: F.bodyBold, fontSize: 14, color: '#FFFFFF' },

  joinPrompt: {
    flex: 1, alignItems: 'center', justifyContent: 'center', padding: 32, gap: 12,
  },
  joinTitle: { fontFamily: F.headingBold, fontSize: 20, color: C.textPrimary, textAlign: 'center' },
  joinSub: { fontFamily: F.bodyRegular, fontSize: 14, color: C.textSecondary },
  joinBtn: { marginTop: 16, paddingHorizontal: 28, paddingVertical: 14, backgroundColor: C.brandPrimary, borderRadius: 14 },
  joinBtnText: { fontFamily: F.bodyBold, fontSize: 15, color: '#FFFFFF' },

  actionBar: {
    position: 'absolute', left: 16, right: 16, bottom: 24,
    flexDirection: 'row', gap: 10,
  },
  readyBtn: {
    flex: 1, paddingVertical: 14, alignItems: 'center', borderRadius: 14,
    backgroundColor: C.brandPrimary,
  },
  readyBtnDone: { backgroundColor: C.success },
  readyBtnText: { fontFamily: F.bodyBold, fontSize: 15, color: '#FFFFFF' },

  diceBtn: { paddingHorizontal: 22, paddingVertical: 14, borderRadius: 14, backgroundColor: C.accentGold },
  diceBtnText: { fontFamily: F.bodyBold, fontSize: 15, color: '#FFFFFF' },
});
