/**
 * Friends — reached from the Messages tab header (no longer a standalone tab).
 *
 * Three sections: incoming requests (with accept/decline buttons), friend
 * groups (with member count), friends list (tap to start a direct chat).
 */

import { router } from 'expo-router';
import { useCallback } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useCreateConversationMutation } from '../api/chatApi';
import {
  useAcceptFriendRequestMutation,
  useDeclineFriendRequestMutation,
  useListFriendGroupsQuery,
  useListFriendsQuery,
  useListIncomingRequestsQuery,
} from '../api/friendsApi';
import { C, F } from '../theme/styleHelpers';

export default function FriendsScreen() {
  const { data: friends = [], isLoading: friendsLoading } = useListFriendsQuery();
  const { data: requests = [], isLoading: reqLoading } = useListIncomingRequestsQuery();
  const { data: groups = [], isLoading: groupsLoading } = useListFriendGroupsQuery();
  const [accept] = useAcceptFriendRequestMutation();
  const [decline] = useDeclineFriendRequestMutation();
  const [createConversation] = useCreateConversationMutation();

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
        <TouchableOpacity onPress={() => router.back()} hitSlop={8}>
          <Text style={s.back}>← Back</Text>
        </TouchableOpacity>
        <Text style={s.title}>🤝 Party</Text>
        <View style={{ width: 52 }} />
      </View>

      <ScrollView contentContainerStyle={s.content}>
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
          <Text style={s.sectionTitle}>Friends ({friends.length})</Text>
          {friendsLoading ? (
            <ActivityIndicator />
          ) : friends.length === 0 ? (
            <Text style={s.empty}>You haven't befriended anyone yet.</Text>
          ) : (
            friends.map((f) => (
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
                <Text style={s.chevron}>💬</Text>
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
  back: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.textSecondary },
  title: { fontFamily: F.headingBold, fontSize: 22, color: C.textPrimary },

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
