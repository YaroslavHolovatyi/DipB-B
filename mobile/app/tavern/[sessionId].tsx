/**
 * Tavern Tales — play screen.
 *
 * The live session with the GPT-4o Dungeon Master. Shows the running message
 * log (your turns right-aligned, the DM's narration left, dice rolls centred),
 * lets you take a turn (POST /tavern/sessions/:id/turn), roll a d20
 * (POST /tavern/sessions/:id/roll) and end the tale (POST .../end).
 *
 * Route: /tavern/[sessionId]
 */

import { Ionicons } from '@expo/vector-icons';
import { router, Stack, useLocalSearchParams } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  useEndSessionMutation,
  useListSessionMessagesQuery,
  useRollDiceMutation,
  useTakeTurnMutation,
} from '../../api/tavernApi';
import type { DndMessage } from '../../api/types';
import { C, F } from '../../theme/styleHelpers';

export default function TavernPlayScreen() {
  const params = useLocalSearchParams<{ sessionId: string }>();
  const sessionId = Number(params.sessionId);

  const {
    data: messages = [],
    isLoading,
    isError,
  } = useListSessionMessagesQuery(sessionId, { skip: !sessionId });

  const [takeTurn, { isLoading: turning }] = useTakeTurnMutation();
  const [rollDice, { isLoading: rolling }] = useRollDiceMutation();
  const [endSession, { isLoading: ending }] = useEndSessionMutation();

  const [draft, setDraft] = useState('');
  const scrollRef = useRef<ScrollView>(null);

  // Keep the log pinned to the latest message.
  useEffect(() => {
    const t = setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 80);
    return () => clearTimeout(t);
  }, [messages.length]);

  const busy = turning || rolling || ending;

  const send = async () => {
    const content = draft.trim();
    if (!content || busy) return;
    setDraft('');
    try {
      await takeTurn({ session_id: sessionId, content }).unwrap();
    } catch {
      setDraft(content);
      Alert.alert('The tale falters', 'Your turn could not be sent — you may have hit your token quota.');
    }
  };

  const roll = async () => {
    if (busy) return;
    const result = Math.floor(Math.random() * 20) + 1;
    try {
      await rollDice({
        session_id: sessionId,
        body: { dice: 'd20', result, purpose: 'check' },
      }).unwrap();
    } catch {
      Alert.alert('The dice slip', 'Could not record your roll. Please try again.');
    }
  };

  const finish = () => {
    Alert.alert('End this tale?', 'You can always begin a new one from the tavern.', [
      { text: 'Keep playing', style: 'cancel' },
      {
        text: 'End tale',
        style: 'destructive',
        onPress: async () => {
          try {
            await endSession({ session_id: sessionId, status: 'completed' }).unwrap();
            router.back();
          } catch {
            Alert.alert('Could not end the tale', 'Please try again.');
          }
        },
      },
    ]);
  };

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <Stack.Screen
        options={{
          title: 'Tavern Tales',
          headerShown: true,
          headerRight: () => (
            <TouchableOpacity onPress={finish} disabled={ending} hitSlop={8}>
              <Text style={s.endLink}>{ending ? '…' : 'End'}</Text>
            </TouchableOpacity>
          ),
        }}
      />

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        {isLoading ? (
          <ActivityIndicator style={{ marginTop: 40 }} />
        ) : isError ? (
          <View style={s.center}>
            <Text style={s.muted}>Couldn&apos;t load this tale.</Text>
          </View>
        ) : (
          <ScrollView
            ref={scrollRef}
            contentContainerStyle={s.log}
            showsVerticalScrollIndicator={false}
          >
            {messages.length === 0 && (
              <Text style={s.muted}>
                The tavern is quiet. Describe your first move to begin the tale…
              </Text>
            )}
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
            {turning && (
              <View style={[s.bubble, s.bubbleDm]}>
                <ActivityIndicator size="small" color={C.brandPrimary} />
              </View>
            )}
          </ScrollView>
        )}

        <View style={s.composer}>
          <TouchableOpacity
            style={[s.diceBtn, busy && s.disabled]}
            onPress={roll}
            disabled={busy}
            activeOpacity={0.85}
          >
            {rolling ? (
              <ActivityIndicator size="small" color={C.accentGoldText} />
            ) : (
              <Ionicons name="dice" size={22} color={C.accentGoldText} />
            )}
          </TouchableOpacity>
          <TextInput
            style={s.input}
            placeholder="What do you do?"
            placeholderTextColor={C.textSecondary}
            value={draft}
            onChangeText={setDraft}
            multiline
            editable={!busy}
          />
          <TouchableOpacity
            style={[s.sendBtn, (!draft.trim() || busy) && s.disabled]}
            onPress={send}
            disabled={!draft.trim() || busy}
            activeOpacity={0.85}
          >
            {turning ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Ionicons name="send" size={18} color="#FFFFFF" />
            )}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function MessageBubble({ message }: { message: DndMessage }) {
  if (message.role === 'dice_roll') {
    return (
      <View style={s.diceRow}>
        <View style={s.dicePill}>
          <Ionicons name="dice" size={13} color={C.accentGoldText} />
          <Text style={s.diceText}>{message.content}</Text>
        </View>
      </View>
    );
  }
  if (message.role === 'system') {
    return (
      <View style={s.diceRow}>
        <Text style={s.systemText}>{message.content}</Text>
      </View>
    );
  }
  const mine = message.role === 'user';
  return (
    <View style={[s.bubble, mine ? s.bubbleMine : s.bubbleDm]}>
      {!mine && <Text style={s.dmLabel}>Dungeon Master</Text>}
      <Text style={[s.bubbleText, mine && s.bubbleTextMine]}>{message.content}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bgBase },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  endLink: { fontFamily: F.bodyBold, fontSize: 15, color: C.error },

  log: { paddingHorizontal: 16, paddingVertical: 16, gap: 12 },
  muted: {
    fontFamily: F.bodyRegular, fontSize: 14, color: C.textSecondary,
    textAlign: 'center', marginTop: 24, paddingHorizontal: 24, lineHeight: 21,
  },

  bubble: {
    maxWidth: '84%', borderRadius: 16, paddingHorizontal: 14, paddingVertical: 11,
  },
  bubbleMine: {
    alignSelf: 'flex-end', backgroundColor: C.brandPrimary, borderBottomRightRadius: 4,
  },
  bubbleDm: {
    alignSelf: 'flex-start', backgroundColor: C.bgCard,
    borderWidth: 1, borderColor: C.borderDefault, borderBottomLeftRadius: 4,
  },
  dmLabel: {
    fontFamily: F.bodyBold, fontSize: 11, color: C.accentGoldText, marginBottom: 4,
    textTransform: 'uppercase', letterSpacing: 0.5,
  },
  bubbleText: { fontFamily: F.bodyRegular, fontSize: 15, color: C.textPrimary, lineHeight: 22 },
  bubbleTextMine: { color: '#FFFFFF' },

  diceRow: { alignItems: 'center', marginVertical: 2 },
  dicePill: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: C.accentGoldSubtle, paddingHorizontal: 12, paddingVertical: 6,
    borderRadius: 999,
  },
  diceText: { fontFamily: F.monoBold, fontSize: 13, color: C.accentGoldText },
  systemText: {
    fontFamily: F.bodyRegular, fontSize: 12, color: C.textSecondary,
    fontStyle: 'italic', textAlign: 'center',
  },

  composer: {
    flexDirection: 'row', alignItems: 'flex-end', gap: 8,
    paddingHorizontal: 12, paddingVertical: 10,
    borderTopWidth: 1, borderTopColor: C.borderDefault, backgroundColor: C.bgCard,
  },
  diceBtn: {
    width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center',
    backgroundColor: C.accentGoldSubtle, borderWidth: 1, borderColor: C.accentGold,
  },
  diceBtnText: { fontSize: 20 },
  input: {
    flex: 1, maxHeight: 120, minHeight: 44,
    fontFamily: F.bodyRegular, fontSize: 15, color: C.textPrimary,
    backgroundColor: C.bgInput, borderRadius: 22,
    borderWidth: 1, borderColor: C.borderDefault,
    paddingHorizontal: 14, paddingVertical: Platform.OS === 'ios' ? 12 : 8,
  },
  sendBtn: {
    width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center',
    backgroundColor: C.brandPrimary,
  },
  sendBtnText: { fontSize: 18, color: '#FFFFFF' },
  disabled: { opacity: 0.45 },
});
