/**
 * Party discovery.
 *
 * Lists open parties, server-sorted by interest match (best match first). Each
 * card shows the title, member count, a "matches your vibe" hint when you share
 * interests, and a "Full" badge when capacity is reached. Tapping opens detail.
 */

import { router } from 'expo-router';
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
import type { Party } from '../../api/types';
import { C, F } from '../../theme/styleHelpers';

export default function PartyListScreen() {
  const { data, isLoading, isFetching, refetch } = useListPartiesQuery({ scope: 'all' });
  const parties = data?.items ?? [];

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()} hitSlop={8}>
          <Text style={s.back}>← Back</Text>
        </TouchableOpacity>
        <Text style={s.title}>Parties</Text>
        <TouchableOpacity onPress={() => router.push('/party/new' as never)} hitSlop={8}>
          <Text style={s.new}>＋ New</Text>
        </TouchableOpacity>
      </View>

      {isLoading ? (
        <ActivityIndicator style={{ marginTop: 40 }} color={C.brandPrimary} />
      ) : (
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
      )}
    </SafeAreaView>
  );
}

function PartyCard({ party }: { party: Party }) {
  const cap = party.max_members ? `${party.member_count}/${party.max_members}` : `${party.member_count}`;
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
          <Text style={s.count}>{cap} 👥</Text>
        )}
      </View>
      {party.description ? (
        <Text style={s.cardDesc} numberOfLines={2}>{party.description}</Text>
      ) : null}
      <View style={s.cardMeta}>
        {party.match_score > 0 && (
          <Text style={s.match}>✨ Matches your vibe ({party.match_score})</Text>
        )}
        {party.drink_match > 0 && <Text style={s.taste}>🍻 Matches your taste</Text>}
        {party.visibility === 'friends_only' && <Text style={s.friends}>Friends only</Text>}
        {party.my_membership === 'joined' && <Text style={s.joined}>Joined</Text>}
      </View>
    </TouchableOpacity>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bgBase },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 20, paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: C.borderDefault,
  },
  back: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.textSecondary },
  title: { fontFamily: F.headingBold, fontSize: 18, color: C.textPrimary },
  new: { fontFamily: F.bodyBold, fontSize: 14, color: C.brandPrimary },

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
  count: { fontFamily: F.bodyBold, fontSize: 13, color: C.textSecondary },
  full: {
    fontFamily: F.bodyBold, fontSize: 12, color: C.error,
    backgroundColor: C.errorSubtle, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8, overflow: 'hidden',
  },
  cardDesc: { fontFamily: F.bodyRegular, fontSize: 13, color: C.textSecondary, lineHeight: 19 },
  cardMeta: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  match: { fontFamily: F.bodySemiBold, fontSize: 12, color: C.brandPrimary },
  taste: { fontFamily: F.bodySemiBold, fontSize: 12, color: C.brandPrimary },
  friends: { fontFamily: F.bodyRegular, fontSize: 12, color: C.textSecondary },
  joined: { fontFamily: F.bodyBold, fontSize: 12, color: C.brandPrimary },
});
