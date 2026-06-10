/**
 * Notifications inbox.
 *
 * Modal-style screen; opens from the bell icon in the Home header. Items are
 * tappable and route to their related entity. Unread rows have a left rail.
 */

import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  useListNotificationsQuery,
  useMarkAllReadMutation,
  useMarkReadMutation,
} from '../api/notificationsApi';
import type { NotificationRead } from '../api/types';
import { C, F } from '../theme/styleHelpers';

function deepLinkFor(n: NotificationRead): string | null {
  if (n.related_entity_type === 'raid' && n.related_entity_id) {
    return `/raids/${n.related_entity_id}`;
  }
  if (n.related_entity_type === 'check' && n.related_entity_id) {
    return `/checks/${n.related_entity_id}`;
  }
  if (n.related_entity_type === 'achievement') {
    return '/profile';
  }
  return null;
}

export default function NotificationsScreen() {
  const { data, isLoading, refetch, isFetching } = useListNotificationsQuery({
    limit: 50,
  });
  const [markRead] = useMarkReadMutation();
  const [markAllRead] = useMarkAllReadMutation();

  const items = data?.items ?? [];
  const anyUnread = items.some((n) => !n.read_at);

  const renderItem = ({ item }: { item: NotificationRead }) => {
    const dest = deepLinkFor(item);
    const unread = !item.read_at;
    return (
      <TouchableOpacity
        style={[s.row, unread && s.rowUnread]}
        activeOpacity={0.85}
        onPress={async () => {
          if (unread) markRead(item.id);
          if (dest) router.push(dest as never);
        }}
      >
        {unread && <View style={s.unreadRail} />}
        <View style={{ flex: 1 }}>
          <Text style={s.title} numberOfLines={1}>
            {item.title}
          </Text>
          {item.body && (
            <Text style={s.body} numberOfLines={2}>
              {item.body}
            </Text>
          )}
          <Text style={s.time}>
            {new Date(item.created_at).toLocaleString()}
          </Text>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()} style={s.backRow}>
          <Ionicons name="chevron-back" size={18} color={C.textSecondary} />
          <Text style={s.back}>Back</Text>
        </TouchableOpacity>
        <View style={s.headerTitleRow}>
          <Ionicons name="notifications" size={16} color={C.textPrimary} />
          <Text style={s.headerTitle}>Inbox</Text>
        </View>
        <TouchableOpacity onPress={() => markAllRead()} disabled={!anyUnread}>
          <Text style={[s.action, !anyUnread && s.actionDisabled]}>
            Mark all
          </Text>
        </TouchableOpacity>
      </View>

      {isLoading ? (
        <ActivityIndicator style={{ marginTop: 40 }} />
      ) : items.length === 0 ? (
        <Text style={s.empty}>You're all caught up.</Text>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(n) => String(n.id)}
          renderItem={renderItem}
          onRefresh={refetch}
          refreshing={isFetching && !isLoading}
          contentContainerStyle={{ paddingBottom: 40 }}
        />
      )}
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bgBase },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 20, paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: C.borderDefault,
  },
  backRow: { flexDirection: 'row', alignItems: 'center', gap: 2 },
  back: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.textSecondary },
  headerTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  headerTitle: { fontFamily: F.headingBold, fontSize: 17, color: C.textPrimary },
  action: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.brandPrimary },
  actionDisabled: { color: C.textDisabled },

  row: {
    flexDirection: 'row', paddingHorizontal: 20, paddingVertical: 14,
    borderBottomWidth: 1, borderBottomColor: C.borderDefault,
    backgroundColor: C.bgCard,
  },
  rowUnread: { backgroundColor: C.brandPrimarySubtle + '40' },
  unreadRail: { width: 3, backgroundColor: C.brandPrimary, marginRight: 12, borderRadius: 2 },

  title: { fontFamily: F.bodyBold, fontSize: 14, color: C.textPrimary },
  body: { fontFamily: F.bodyRegular, fontSize: 13, color: C.textSecondary, marginTop: 2 },
  time: { fontFamily: F.bodyRegular, fontSize: 11, color: C.textDisabled, marginTop: 4 },

  empty: {
    fontFamily: F.bodyRegular, fontSize: 14, color: C.textSecondary,
    textAlign: 'center', paddingTop: 40,
  },
});
