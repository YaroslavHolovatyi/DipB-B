/**
 * Social — discovery for raids and parties.
 *
 * A segmented filter switches between Raids (time-boxed tavern meetups) and
 * Parties (interest-matched open invites). Both feeds are server-sorted by
 * match (shared interests / taste first). Tapping a card opens its detail.
 *
 * The header avatar opens the Profile screen (Profile is no longer a tab).
 */

import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useListPartiesQuery } from '../../api/partiesApi';
import { useListRaidsQuery } from '../../api/raidsApi';
import type { Party, Raid } from '../../api/types';
import { useAppSelector } from '../../store';
import { C, F } from '../../theme/styleHelpers';

type Feed = 'raids' | 'parties';

function whenLabel(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleString(undefined, {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function SocialScreen() {
  const [feed, setFeed] = useState<Feed>('raids');
  const user = useAppSelector((s) => s.auth.user);

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <View style={s.headerRow}>
        <View style={s.titleRow}>
          <Ionicons name="sparkles" size={20} color={C.textPrimary} />
          <Text style={s.title}>Social</Text>
        </View>
        <TouchableOpacity
          onPress={() => router.push('/profile' as never)}
          activeOpacity={0.85}
          hitSlop={8}
        >
          <View style={s.avatar}>
            {user?.first_name?.[0] ? (
              <Text style={s.avatarInitial}>{user.first_name[0].toUpperCase()}</Text>
            ) : (
              <Ionicons name="person" size={16} color={C.brandPrimaryHover} />
            )}
          </View>
        </TouchableOpacity>
      </View>

      <View style={s.segmentRow}>
        {(['raids', 'parties'] as Feed[]).map((f) => {
          const active = feed === f;
          return (
            <TouchableOpacity
              key={f}
              onPress={() => setFeed(f)}
              style={[s.segment, active && s.segmentActive]}
              activeOpacity={0.85}
            >
              <Ionicons
                name={f === 'raids' ? 'flag' : 'beer'}
                size={15}
                color={active ? '#FFFFFF' : C.textSecondary}
              />
              <Text style={[s.segmentText, active && s.segmentTextActive]}>
                {f === 'raids' ? 'Raids' : 'Parties'}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {feed === 'raids' ? <RaidFeed /> : <PartyFeed />}
    </SafeAreaView>
  );
}

// ── Raids ─────────────────────────────────────────────────────────────────────
function RaidFeed() {
  const { data, isLoading, isFetching, refetch } = useListRaidsQuery({ scope: 'all' });
  const raids = data?.items ?? [];

  if (isLoading) return <ActivityIndicator style={{ marginTop: 40 }} color={C.brandPrimary} />;

  return (
    <FlatList
      data={raids}
      keyExtractor={(r) => String(r.id)}
      contentContainerStyle={s.list}
      refreshControl={
        <RefreshControl refreshing={isFetching} onRefresh={refetch} tintColor={C.brandPrimary} />
      }
      ListEmptyComponent={
        <View style={s.empty}>
          <Text style={s.emptyText}>No raids yet. Rally one!</Text>
        </View>
      }
      renderItem={({ item }) => <RaidCard raid={item} />}
    />
  );
}

function RaidCard({ raid }: { raid: Raid }) {
  const isFull =
    raid.max_participants != null && raid.participant_count >= raid.max_participants;
  const cap = raid.max_participants
    ? `${raid.participant_count}/${raid.max_participants}`
    : `${raid.participant_count}`;

  return (
    <TouchableOpacity
      style={s.card}
      onPress={() => router.push(`/raids/${raid.id}` as never)}
      activeOpacity={0.85}
    >
      <View style={s.cardTop}>
        <Text style={s.cardTitle} numberOfLines={1}>{raid.title}</Text>
        {isFull ? (
          <Text style={s.full}>Full</Text>
        ) : (
          <View style={s.countRow}>
            <Text style={s.count}>{cap}</Text>
            <Ionicons name="people" size={13} color={C.textSecondary} />
          </View>
        )}
      </View>
      <View style={s.whenRow}>
        <Ionicons name="time-outline" size={13} color={C.textSecondary} />
        <Text style={s.cardWhen}>{whenLabel(raid.scheduled_at)}</Text>
      </View>
      {raid.theme ? <Text style={s.cardDesc} numberOfLines={1}>{raid.theme}</Text> : null}
      <View style={s.cardMeta}>
        {raid.drink_match > 0 && (
          <View style={s.metaRow}>
            <Ionicons name="beer" size={12} color={C.accentGoldText} />
            <Text style={s.taste}>Matches your taste</Text>
          </View>
        )}
        {raid.visibility === 'friends_only' && <Text style={s.friends}>Friends only</Text>}
        {raid.my_rsvp === 'going' && <Text style={s.joined}>Going</Text>}
        <Text style={s.statusPill}>{raid.status}</Text>
      </View>
    </TouchableOpacity>
  );
}

// ── Parties ───────────────────────────────────────────────────────────────────
function PartyFeed() {
  const { data, isLoading, isFetching, refetch } = useListPartiesQuery({ scope: 'all' });
  const parties = data?.items ?? [];

  if (isLoading) return <ActivityIndicator style={{ marginTop: 40 }} color={C.brandPrimary} />;

  return (
    <FlatList
      data={parties}
      keyExtractor={(p) => String(p.id)}
      contentContainerStyle={s.list}
      refreshControl={
        <RefreshControl refreshing={isFetching} onRefresh={refetch} tintColor={C.brandPrimary} />
      }
      ListEmptyComponent={
        <View style={s.empty}>
          <Text style={s.emptyText}>No parties yet. Start one!</Text>
        </View>
      }
      renderItem={({ item }) => <PartyCard party={item} />}
    />
  );
}

function PartyCard({ party }: { party: Party }) {
  const cap = party.max_members
    ? `${party.member_count}/${party.max_members}`
    : `${party.member_count}`;
  return (
    <TouchableOpacity
      style={s.card}
      onPress={() => router.push(`/party/${party.id}` as never)}
      activeOpacity={0.85}
    >
      <View style={s.cardTop}>
        <Text style={s.cardTitle} numberOfLines={1}>{party.title}</Text>
        {party.is_full ? (
          <Text style={s.full}>Full</Text>
        ) : (
          <View style={s.countRow}>
            <Text style={s.count}>{cap}</Text>
            <Ionicons name="people" size={13} color={C.textSecondary} />
          </View>
        )}
      </View>
      {party.description ? (
        <Text style={s.cardDesc} numberOfLines={2}>{party.description}</Text>
      ) : null}
      <View style={s.cardMeta}>
        {party.match_score > 0 && (
          <View style={s.metaRow}>
            <Ionicons name="sparkles" size={12} color={C.brandPrimary} />
            <Text style={s.match}>Matches your vibe ({party.match_score})</Text>
          </View>
        )}
        {party.drink_match > 0 && (
          <View style={s.metaRow}>
            <Ionicons name="beer" size={12} color={C.accentGoldText} />
            <Text style={s.taste}>Matches your taste</Text>
          </View>
        )}
        {party.visibility === 'friends_only' && <Text style={s.friends}>Friends only</Text>}
        {party.my_membership === 'joined' && <Text style={s.joined}>Joined</Text>}
      </View>
    </TouchableOpacity>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bgBase },

  headerRow: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 20, paddingTop: 12, paddingBottom: 8,
  },
  titleRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  title: { fontFamily: F.headingBold, fontSize: 22, color: C.textPrimary },
  avatar: {
    width: 34, height: 34, borderRadius: 17,
    backgroundColor: C.brandPrimarySubtle, alignItems: 'center', justifyContent: 'center',
    borderWidth: 1, borderColor: C.borderDefault,
  },
  avatarInitial: { fontFamily: F.headingBold, fontSize: 15, color: C.brandPrimaryHover },

  segmentRow: { flexDirection: 'row', gap: 10, paddingHorizontal: 20, paddingBottom: 8 },
  segment: {
    flex: 1, paddingVertical: 9, borderRadius: 10,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6,
    backgroundColor: C.bgCard, borderWidth: 1, borderColor: C.borderDefault,
  },
  segmentActive: { backgroundColor: C.brandPrimary, borderColor: C.brandPrimary },
  segmentText: { fontFamily: F.bodyBold, fontSize: 14, color: C.textSecondary },
  segmentTextActive: { color: '#FFFFFF' },

  list: { padding: 16, gap: 12 },
  empty: { paddingTop: 60, alignItems: 'center' },
  emptyText: { fontFamily: F.bodyRegular, fontSize: 14, color: C.textSecondary },

  card: {
    padding: 16, borderRadius: 14,
    backgroundColor: C.bgCard, borderWidth: 1, borderColor: C.borderDefault,
    gap: 8,
  },
  cardTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  cardTitle: { flex: 1, fontFamily: F.headingSemi, fontSize: 16, color: C.textPrimary },
  whenRow: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  cardWhen: { fontFamily: F.bodySemiBold, fontSize: 12, color: C.textSecondary },
  countRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  count: { fontFamily: F.bodyBold, fontSize: 13, color: C.textSecondary },
  full: {
    fontFamily: F.bodyBold, fontSize: 12, color: C.error,
    backgroundColor: C.errorSubtle, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8, overflow: 'hidden',
  },
  cardDesc: { fontFamily: F.bodyRegular, fontSize: 13, color: C.textSecondary, lineHeight: 19 },
  cardMeta: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 10 },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  match: { fontFamily: F.bodySemiBold, fontSize: 12, color: C.brandPrimary },
  taste: { fontFamily: F.bodySemiBold, fontSize: 12, color: C.brandPrimary },
  friends: { fontFamily: F.bodyRegular, fontSize: 12, color: C.textSecondary },
  joined: { fontFamily: F.bodyBold, fontSize: 12, color: C.brandPrimary },
  statusPill: {
    fontFamily: F.bodySemiBold, fontSize: 11, color: C.textSecondary,
    backgroundColor: C.bgInput, paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8, overflow: 'hidden',
  },
});
