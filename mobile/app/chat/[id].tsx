/**
 * Chat thread.
 *
 * Polls /chat/conversations/{id}/messages on mount and then relies on the WS
 * `message.new` events to keep the list fresh (those events patch the cache
 * directly — see `lib/ws.ts`).
 *
 * On mount and after every new message arrives we POST `/chat/.../read` so
 * other participants see the read tick.
 */

import { router, useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  useGetConversationQuery,
  useListMessagesQuery,
  useMarkConversationReadMutation,
  useSendMessageMutation,
} from '../../api/chatApi';
import type { ChatMessage } from '../../api/types';
import { useAppSelector } from '../../store';
import { C, F } from '../../theme/styleHelpers';

export default function ChatThreadScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const conversationId = Number(id);

  const myId = useAppSelector((s) => s.auth.user?.id);

  const { data: convo } = useGetConversationQuery(conversationId, {
    skip: !conversationId,
  });
  const { data: messages = [], isLoading } = useListMessagesQuery(
    { conversation_id: conversationId, limit: 50 },
    { skip: !conversationId },
  );
  const [sendMessage] = useSendMessageMutation();
  const [markRead] = useMarkConversationReadMutation();

  const [text, setText] = useState('');
  const [sendError, setSendError] = useState(false);
  const listRef = useRef<FlatList>(null);

  // Mark up-to-newest as read whenever the message list changes.
  useEffect(() => {
    const newest = messages[messages.length - 1];
    if (newest) {
      markRead({ conversation_id: conversationId, up_to_message_id: newest.id });
    }
  }, [messages, conversationId, markRead]);

  const handleSend = useCallback(async () => {
    const body = text.trim();
    if (!body) return;
    setText('');
    setSendError(false);
    try {
      await sendMessage({
        conversation_id: conversationId,
        body: { body },
      }).unwrap();
    } catch {
      // restore text so the user doesn't lose it, and surface the failure
      setText(body);
      setSendError(true);
    }
  }, [text, sendMessage, conversationId]);

  const renderItem = useCallback(
    ({ item }: { item: ChatMessage }) => {
      const mine = item.sender_id === myId;
      return (
        <View style={[bubble.row, mine && bubble.rowMine]}>
          <View style={[bubble.box, mine ? bubble.boxMine : bubble.boxTheirs]}>
            {item.body && (
              <Text style={[bubble.text, mine && bubble.textMine]}>{item.body}</Text>
            )}
            <Text style={[bubble.meta, mine && bubble.metaMine]}>
              {new Date(item.created_at).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </Text>
          </View>
        </View>
      );
    },
    [myId],
  );

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={s.back}>← Back</Text>
        </TouchableOpacity>
        <Text style={s.title} numberOfLines={1}>
          {convo?.title ?? (convo?.type === 'direct' ? 'Direct chat' : 'Conversation')}
        </Text>
        <View style={{ width: 50 }} />
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={s.kav}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 80 : 0}
      >
        {isLoading ? (
          <ActivityIndicator style={{ marginTop: 40 }} />
        ) : (
          <FlatList
            ref={listRef}
            data={messages}
            keyExtractor={(m) => String(m.id)}
            renderItem={renderItem}
            contentContainerStyle={s.listContent}
            onContentSizeChange={() =>
              listRef.current?.scrollToEnd({ animated: true })
            }
          />
        )}

        {sendError && (
          <Text style={s.sendError}>Couldn't send — check your connection and try again.</Text>
        )}
        <View style={s.composer}>
          <TextInput
            value={text}
            onChangeText={setText}
            placeholder="Message…"
            placeholderTextColor={C.textSecondary}
            style={s.input}
            multiline
          />
          <TouchableOpacity
            onPress={handleSend}
            style={[s.sendBtn, !text.trim() && s.sendBtnDisabled]}
            disabled={!text.trim()}
          >
            <Text style={s.sendText}>Send</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const bubble = StyleSheet.create({
  row: { flexDirection: 'row', paddingHorizontal: 12, paddingVertical: 4 },
  rowMine: { justifyContent: 'flex-end' },
  box: { maxWidth: '76%', borderRadius: 14, paddingHorizontal: 12, paddingVertical: 8 },
  boxTheirs: { backgroundColor: C.bgCard, borderColor: C.borderDefault, borderWidth: 1 },
  boxMine: { backgroundColor: C.brandPrimary },
  text: { fontFamily: F.bodyRegular, fontSize: 14, color: C.textPrimary },
  textMine: { color: '#FFFFFF' },
  meta: { fontFamily: F.bodyRegular, fontSize: 10, color: C.textSecondary, marginTop: 4 },
  metaMine: { color: 'rgba(255,255,255,0.7)' },
});

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bgBase },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: C.borderDefault,
  },
  back: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.textSecondary, width: 60 },
  title: { fontFamily: F.headingBold, fontSize: 16, color: C.textPrimary, flex: 1, textAlign: 'center' },

  kav: { flex: 1 },
  listContent: { paddingVertical: 8 },

  sendError: {
    fontFamily: F.bodyRegular, fontSize: 12, color: '#D9534F',
    textAlign: 'center', paddingVertical: 4, backgroundColor: C.bgCard,
  },
  composer: {
    flexDirection: 'row', alignItems: 'flex-end', gap: 8,
    padding: 12, borderTopWidth: 1, borderTopColor: C.borderDefault, backgroundColor: C.bgCard,
  },
  input: {
    flex: 1, maxHeight: 120, fontFamily: F.bodyRegular, fontSize: 15, color: C.textPrimary,
    paddingHorizontal: 12, paddingVertical: 10,
    backgroundColor: C.bgInput, borderRadius: 18,
  },
  sendBtn: { backgroundColor: C.brandPrimary, paddingHorizontal: 16, paddingVertical: 10, borderRadius: 18 },
  sendBtnDisabled: { backgroundColor: C.brandPrimary + '60' },
  sendText: { fontFamily: F.bodyBold, fontSize: 14, color: '#FFFFFF' },
});
