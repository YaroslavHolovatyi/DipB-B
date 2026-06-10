/**
 * Friends — reached from the Messages tab header (no longer a standalone tab).
 *
 * Three sections: incoming requests (with accept/decline buttons), friend
 * groups (with member count), friends list (tap to start a direct chat).
 */

import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useCreateConversationMutation } from '../api/chatApi';
import {
  useAcceptFriendRequestMutation,
  useCancelFriendRequestMutation,
  useDeclineFriendRequestMutation,
  useListFriendGroupsQuery,
  useListFriendsQuery,
  useListIncomingRequestsQuery,
  useSearchUsersQuery,
  useSendFriendRequestMutation,
} from '../api/friendsApi';
import { C, F } from '../theme/styleHelpers';

/** Debounce a string value so we don't hit /friends/search on every keystroke. */
function useDebounced(value: string, delayMs = 300): string {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(t);
  }, [value, delayMs]);
  return debounced;
}

export default function FriendsScreen() {
  const { data: friends = [], isLoading: friendsLoading } = useListFriendsQuery();
  const { data: requests = [], isLoading: reqLoading } = useListIncomingRequestsQuery();
  const { data: groups = [], isLoading: groupsLoading } = useListFriendGroupsQuery();
  const [accept] = useAcceptFriendRequestMutation();
  const [decline] = useDeclineFriendRequestMutation();
  const [sendRequest] = useSendFriendRequestMutation();
  const [cancelRequest] = useCancelFriendRequestMutation();
  const [createConversation] = useCreateConversationMutation();

  // ── Search ────────────────────────────────────────────────────────────────
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounced(query.trim());
  const searching = debouncedQuery.length >= 2;

  // Local filter over my friends list (name, surname, username, nickname).
  const filteredFriends = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return friends;
    return friends.filter((f) => {
      const hay = [
        f.user.first_name,
        f.user.last_name ?? '',
        f.user.username,
        f.nickname ?? '',
      ]
        .join(' ')
        .toLowerCase();
      return hay.includes(q);
    });
  }, [friends, query]);

  // Global user search — only people who aren't my friends yet are shown
  // (friends already appear in the filtered list above).
  const { data: searchResults = [], isFetching: searchLoading } =
    useSearchUsersQuery(debouncedQuery, { skip: !searching });
  const discoverable = useMemo(
    () => searchResults.filter((r) => r.relationship !== 'friend'),
    [searchResults],
  );

  const startChat = useCallback(
    async (otherUserId: number) => {
      try {
        const convo = await createConversation({
          type: 'direct',
          participant_ids: [otherUserId],
        }).unwrap();
        router.push(`/chat/${convo.id}` as never);
      } catch {
        /* surface via toast in a future iteration */
      }
    },
    [createConversation],
  );

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <View style={s.headerRow}>
        <TouchableOpacity onPress={() => router.back()} hitSlop={8} style={s.backRow}>
          <Ionicons name="chevron-back" size={18} color={C.textSecondary} />
          <Text style={s.back}>Back</Text>
        </TouchableOpacity>
        <View style={s.titleRow}>
          <Ionicons name="people" size={16} color={C.textPrimary} />
          <Text style={s.title}>Party</Text>
        </View>
        <View style={{ width: 52 }} />
      </View>

      <View style={s.searchWrap}>
        <Ionicons name="search" size={16} color={C.textSecondary} />
        <TextInput
          value={query}
          onChangeText={setQuery}
          placeholder="Search friends or find adventurers…"
          placeholderTextColor={C.textSecondary}
          style={s.searchInput}
          autoCapitalize="none"
          autoCorrect={false}
          returnKeyType="search"
        />
        {query.length > 0 && (
          <TouchableOpacity onPress={() => setQuery('')} hitSlop={8}>
            <Ionicons name="close-circle" size={16} color={C.textSecondary} />
          </TouchableOpacity>
        )}
      </View>

      <ScrollView contentContainerStyle={s.content} keyboardShouldPersistTaps="handled">
        {searching && (
          <View style={s.section}>
            <Text style={s.sectionTitle}>Find adventurers</Text>
            {searchLoading ? (
              <ActivityIndicator />
            ) : discoverable.length === 0 ? (
              <Text style={s.empty}>No new adventurers match “{debouncedQuery}”.</Text>
            ) : (
              discoverable.map((r) => (
                <View key={r.user.id} style={s.requestRow}>
                  <View style={s.avatar}>
                    <Text style={s.avatarInitial}>
                      {r.user.first_name[0]?.toUpperCase()}
                    </Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={s.rowName}>
                      {r.user.first_name} {r.user.last_name ?? ''}
                    </Text>
                    <Text style={s.rowSub}>@{r.user.username}</Text>
                  </View>
                  {r.relationship === 'none' && (
                    <TouchableOpacity
                      style={s.acceptBtn}
                      onPress={() => sendRequest({ recipient_id: r.user.id })}
                    >
                      <Text style={s.acceptText}>Add</Text>
                    </TouchableOpacity>
                  )}
                  {r.relationship === 'outgoing' && (
                    <TouchableOpacity
                      style={s.declineBtn}
                      onPress={() => r.request_id && cancelRequest(r.request_id)}
                    >
                      <Text style={s.declineText}>Pending · Cancel</Text>
                    </TouchableOpacity>
                  )}
                  {r.relationship === 'incoming' && (
                    <TouchableOpacity
                      style={s.acceptBtn}
                      onPress={() => r.request_id && accept(r.request_id)}
                    >
                      <Text style={s.acceptText}>Accept</Text>
                    </TouchableOpacity>
                  )}
                </View>
              ))
            )}
          </View>
        )}

        {requests.length > 0 && (
          <View style={s.section}>
            <Text style={s.sectionTitle}>Incoming requests</Text>
            {reqLoading ? (
              <ActivityIndicator />
            ) : (
              requests.map((r) => (
                <View key={r.id} style={s.requestRow}>
                  <View style={{ flex: 1 }}>
                    <Text style={s.rowName}>From user #{r.sender_id}</Text>
                    {r.message && <Text style={s.rowSub}>{r.message}</Text>}
                  </View>
                  <TouchableOpacity style={s.acceptBtn} onPress={() => accept(r.id)}>
                    <Text style={s.acceptText}>Accept</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={s.declineBtn} onPress={() => decline(r.id)}>
                    <Text style={s.declineText}>Decline</Text>
                  </TouchableOpacity>
                </View>
              ))
            )}
          </View>
        )}

        <View style={s.section}>
          <Text style={s.sectionTitle}>Parties for Dungeon</Text>
          {groupsLoading ? (
            <ActivityIndicator />
          ) : groups.length === 0 ? (
            <Text style={s.empty}>No parties yet — gather your finest, adventurer.</Text>
          ) : (
            groups.map((g) => (
              <View key={g.id} style={s.groupRow}>
                <View style={s.groupAvatar}>
                  <Text style={s.groupInitial}>{g.name[0]?.toUpperCase()}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={s.rowName}>{g.name}</Text>
                  <Text style={s.rowSub}>{g.member_count} members</Text>
                </View>
              </View>
            ))
          )}
        </View>

        <View style={s.section}>
          <Text style={s.sectionTitle}>
            Friends ({query.trim() ? `${filteredFriends.length}/${friends.length}` : friends.length})
          </Text>
          {friendsLoading ? (
            <ActivityIndicator />
          ) : filteredFriends.length === 0 ? (
            <Text style={s.empty}>
              {query.trim()
                ? `No friends match “${query.trim()}”.`
                : "You haven't befriended anyone yet."}
            </Text>
          ) : (
            filteredFriends.map((f) => (
              <TouchableOpacity
                key={f.user.id}
                style={s.friendRow}
                activeOpacity={0.85}
                onPress={() => startChat(f.user.id)}
              >
                <View style={s.avatar}>
                  <Text style={s.avatarInitial}>
                    {f.user.first_name[0]?.toUpperCase()}
                  </Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={s.rowName}>
                    {f.user.first_name} {f.user.last_name ?? ''}
                  </Text>
                  <Text style={s.rowSub}>@{f.user.username}</Text>
                </View>
                <Ionicons name="chatbubble-ellipses" size={20} color={C.brandPrimary} />
              </TouchableOpacity>
            ))
          )}
        </View>

        <View style={{ height: 60 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bgBase },
  headerRow: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 20, paddingTop: 12, paddingBottom: 8,
  },
  backRow: { flexDirection: 'row', alignItems: 'center', gap: 2 },
  back: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.textSecondary },
  titleRow: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  title: { fontFamily: F.headingBold, fontSize: 22, color: C.textPrimary },

  searchWrap: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    marginHorizontal: 20, marginTop: 4, marginBottom: 4,
    paddingHorizontal: 12, paddingVertical: 8,
    backgroundColor: C.bgInput, borderRadius: 12,
    borderWidth: 1, borderColor: C.borderDefault,
  },
  searchInput: {
    flex: 1, fontFamily: F.bodyRegular, fontSize: 14, color: C.textPrimary,
    paddingVertical: 0,
  },

  content: { paddingHorizontal: 20, paddingBottom: 80 },

  section: { marginTop: 12, marginBottom: 8 },
  sectionTitle: {
    fontFamily: F.headingSemi, fontSize: 15, color: C.textPrimary,
    marginBottom: 10, letterSpacing: 0.2,
  },

  empty: { fontFamily: F.bodyRegular, fontSize: 13, color: C.textSecondary, paddingVertical: 8 },

  requestRow: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    paddingVertical: 12, paddingHorizontal: 12,
    backgroundColor: C.bgCard, borderColor: C.borderDefault, borderWidth: 1,
    borderRadius: 12, marginBottom: 8,
  },
  acceptBtn: { backgroundColor: C.brandPrimary, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8 },
  acceptText: { color: '#FFFFFF', fontFamily: F.bodyBold, fontSize: 13 },
  declineBtn: { backgroundColor: C.bgInput, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8 },
  declineText: { color: C.textSecondary, fontFamily: F.bodySemiBold, fontSize: 13 },

  groupRow: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    paddingVertical: 10, paddingHorizontal: 12,
    backgroundColor: C.bgCard, borderColor: C.borderDefault, borderWidth: 1,
    borderRadius: 12, marginBottom: 8,
  },
  groupAvatar: {
    width: 44, height: 44, borderRadius: 22,
    backgroundColor: C.brandPrimarySubtle,
    alignItems: 'center', justifyContent: 'center',
  },
  groupInitial: { fontFamily: F.headingBold, fontSize: 18, color: C.brandPrimaryHover },

  friendRow: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: C.borderDefault,
  },
  avatar: {
    width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center',
    backgroundColor: C.raceElfBg,
  },
  avatarInitial: { fontFamily: F.headingBold, fontSize: 18, color: C.raceElfText },

  rowName: { fontFamily: F.bodyBold, fontSize: 14, color: C.textPrimary },
  rowSub: { fontFamily: F.bodyRegular, fontSize: 12, color: C.textSecondary, marginTop: 1 },
  chevron: { fontSize: 18 },
});
