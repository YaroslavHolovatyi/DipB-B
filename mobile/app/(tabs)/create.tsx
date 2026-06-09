/**
 * Create — chooser hub.
 *
 * A simple landing that routes to the two creation flows: host a Raid
 * (time-boxed tavern meetup) or start a Party (interest-matched open invite).
 * Both open as modals registered in the root stack.
 */

import { router } from 'expo-router';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { C, F } from '../../theme/styleHelpers';

export default function CreateScreen() {
  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <View style={s.header}>
        <Text style={s.title}>➕ Create</Text>
        <Text style={s.subtitle}>What are you rallying today?</Text>
      </View>

      <View style={s.cards}>
        <TouchableOpacity
          style={[s.card, s.raidCard]}
          onPress={() => router.push('/raids/new' as never)}
          activeOpacity={0.9}
        >
          <Text style={s.cardEmoji}>🗡️</Text>
          <Text style={s.cardTitle}>Host a Raid</Text>
          <Text style={s.cardBody}>
            Pick a tavern and a time. Friends and nearby adventurers RSVP and
            check in on the night.
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[s.card, s.partyCard]}
          onPress={() => router.push('/party/new' as never)}
          activeOpacity={0.9}
        >
          <Text style={s.cardEmoji}>🍻</Text>
          <Text style={s.cardTitle}>Start a Party</Text>
          <Text style={s.cardBody}>
            Gather people by shared interests and taste. Open to all or just
            your friends.
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bgBase },

  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 4 },
  title: { fontFamily: F.headingBold, fontSize: 24, color: C.textPrimary },
  subtitle: { fontFamily: F.bodyRegular, fontSize: 14, color: C.textSecondary, marginTop: 4 },

  cards: { padding: 20, gap: 16 },
  card: {
    padding: 20, borderRadius: 18,
    borderWidth: 1, borderColor: C.borderDefault, gap: 8,
  },
  raidCard: { backgroundColor: C.brandPrimarySubtle },
  partyCard: { backgroundColor: C.accentGoldSubtle },
  cardEmoji: { fontSize: 40 },
  cardTitle: { fontFamily: F.headingBold, fontSize: 20, color: C.textPrimary },
  cardBody: { fontFamily: F.bodyRegular, fontSize: 14, color: C.textSecondary, lineHeight: 21 },
});
