/**
 * Messages — the conversation list.
 *
 * One feed for every chat you're in: friend DMs, party / group chats, and raid
 * chats. We tag each row by kind (a raid_id marks a raid chat; a friend_group_id
 * marks a group/party chat; otherwise it's a direct message). Direct-chat names
 * are resolved from the friends list since the API returns participant ids only.
 *
 * Tapping a row opens /chat/[id]. The header "Friends" action reaches the friend
 * roster + requests (to start new direct chats).
 */

import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { ComponentProps, useMemo } from 'react';
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

import { useListConversationsQuery } from '../../api/chatApi';
import { useListFriendsQuery } from '../../api/friendsApi';
import type { Conversation } from '../../api/types';
import { useAppSelector } from '../../store';
import { C, F } from '../../theme/styleHelpers';

type Kind = 'raid' | 'group' | 'direct';

function kindOf(c: Conversation): Kind {
  if (c.raid_id != null) return 'raid';
  if (c.friend_group_id != null || c.type === 'group') return 'group';
  return 'direct';
}

type IoniconName = ComponentProps<typeof Ionicons>['name'];

const KIND_META: Record<Kind, { icon: IoniconName; tag: string }> = {
  raid: { icon: 'flag', tag: 'Raid' },
  group: { icon: 'shield-half', tag: 'Party' },
  direct: { icon: 'chatbubble-ellipses', tag: 'Direct' },
};

function timeLabel(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const now = new Date();
  const sameDay = d.toDateString() === now.toDateString();
  return sameDay
    ? d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
    : d.toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
}

export default function MessagesScreen() {
  const myId = useAppSelector((s) => s.auth.user?.id);
  const { data: conversations = [], isLoading, isFetching, refetch } =
    useListConversationsQuery();
  const { data: friends = [] } = useListFriendsQuery();

  // id → display name, for resolving direct-chat titles.
  const friendName = useMemo(() => {
    const m = new Map<number, string>();
    for (const f of friends) {
      m.set(f.user.id, `${f.user.first_name}${f.user.last_name ? ` ${f.user.last_name}` : ''}`);
    }
    return m;
  }, [friends]);

  const sorted = useMemo(
    () =>
      [...conversations].sort((a, b) =>
        (b.last_message_at ?? '').localeCompare(a.last_message_at ?? ''),
      ),
    [conversations],
  );

  const titleFor = (c: Conversation): string => {
    if (c.title?.trim()) return c.title.trim();
    if (kindOf(c) === 'direct' && myId != null) {
      const other = c.participants.find((p) => p !== myId);
      if (other != null && friendName.has(other)) return friendName.get(other)!;
      return other != null ? `User #${other}` : 'Direct chat';
    }
    return KIND_META[kindOf(c)].tag;
  };

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <View style={s.headerRow}>
        <View style={s.titleRow}>
          <Ionicons name="chatbubbles" size={20} color={C.textPrimary} />
          <Text style={s.title}>Messages</Text>
        </View>
        <TouchableOpacity
          onPress={() => router.push('/friends' as never)}
          activeOpacity={0.85}
          hitSlop={8}
          style={s.actionRow}
        >
          <Ionicons name="people" size={15} color={C.brandPrimary} />
          <Text style={s.action}>Friends</Text>
        </TouchableOpacity>
      </View>

      {isLoading ? (
        <ActivityIndicator style={{ marginTop: 40 }} color={C.brandPrimary} />
      ) : (
        <FlatList
          data={sorted}
          keyExtractor={(c) => String(c.id)}
          contentContainerStyle={s.list}
          refreshControl={
            <RefreshControl refreshing={isFetching} onRefresh={refetch} tintColor={C.brandPrimary} />
          }
          ListEmptyComponent={
            <View style={s.empty}>
              <Text style={s.emptyText}>No conversations yet.</Text>
              <TouchableOpacity onPress={() => router.push('/friends' as never)} activeOpacity={0.85}>
                <Text style={s.emptyAction}>Find friends to chat with</Text>
              </TouchableOpacity>
            </View>
          }
          renderItem={({ item }) => {
            const kind = kindOf(item);
            const meta = KIND_META[kind];
            return (
              <TouchableOpacity
                style={s.row}
                activeOpacity={0.85}
                onPress={() => router.push(`/chat/${item.id}` as never)}
              >
                <View style={s.avatar}>
                  <Ionicons name={meta.icon} size={20} color={C.brandPrimaryHover} />
                </View>
                <View style={{ flex: 1 }}>
                  <View style={s.rowTop}>
                    <Text style={s.rowName} numberOfLines={1}>{titleFor(item)}</Text>
                    <Text style={s.time}>{timeLabel(item.last_message_at)}</Text>
                  </View>
                  <View style={s.rowBottom}>
                    <Text style={s.preview} numberOfLines={1}>
                      {item.last_message_preview ?? 'No messages yet'}
                    </Text>
                    {item.unread_count > 0 && (
                      <View style={s.badge}>
                        <Text style={s.badgeText}>
                          {item.unread_count > 99 ? '99+' : item.unread_count}
                        </Text>
                      </View>
                    )}
                  </View>
                  {kind !== 'direct' && <Text style={s.tag}>{meta.tag}</Text>}
                </View>
              </TouchableOpacity>
            );
          }}
        />
      )}
    </SafeAreaView>
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
  actionRow: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  action: { fontFamily: F.bodyBold, fontSize: 14, color: C.brandPrimary },

  list: { paddingHorizontal: 16, paddingTop: 4, paddingBottom: 100 },

  empty: { paddingTop: 60, alignItems: 'center', gap: 10 },
  emptyText: { fontFamily: F.bodyRegular, fontSize: 14, color: C.textSecondary },
  emptyAction: { fontFamily: F.bodyBold, fontSize: 14, color: C.brandPrimary },

  row: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    paddingVertical: 12, paddingHorizontal: 8,
    borderBottomWidth: 1, borderBottomColor: C.borderDefault,
  },
  avatar: {
    width: 48, height: 48, borderRadius: 24,
    backgroundColor: C.bgCard, borderWidth: 1, borderColor: C.borderDefault,
    alignItems: 'center', justifyContent: 'center',
  },
  avatarEmoji: { fontSize: 22 },

  rowTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  rowName: { flex: 1, fontFamily: F.bodyBold, fontSize: 15, color: C.textPrimary },
  time: { fontFamily: F.bodyRegular, fontSize: 11, color: C.textSecondary },

  rowBottom: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginTop: 2 },
  preview: { flex: 1, fontFamily: F.bodyRegular, fontSize: 13, color: C.textSecondary },
  badge: {
    minWidth: 20, height: 20, borderRadius: 10, paddingHorizontal: 6,
    backgroundColor: C.brandPrimary, alignItems: 'center', justifyContent: 'center',
  },
  badgeText: { fontFamily: F.bodyBold, fontSize: 11, color: '#FFFFFF' },

  tag: {
    alignSelf: 'flex-start', marginTop: 4,
    fontFamily: F.bodySemiBold, fontSize: 10, color: C.textSecondary,
    backgroundColor: C.bgInput, paddingHorizontal: 7, paddingVertical: 2,
    borderRadius: 6, overflow: 'hidden',
  },
});
