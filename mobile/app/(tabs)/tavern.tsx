/**
 * Tavern Tales — AI D&D tab.
 *
 * The single-player GPT-4o "AI Dungeon Master". From here you can:
 *   - see your daily/monthly token quota,
 *   - forge a hero (name + class) via POST /tavern/characters,
 *   - begin a tale (POST /tavern/sessions) and jump into the play screen.
 *
 * The play screen lives at /tavern/[sessionId].
 */

import { router } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  useCreateCharacterMutation,
  useCreateSessionMutation,
  useListCharactersQuery,
  useListClassesQuery,
  useQuotaQuery,
} from '../../api/tavernApi';
import type { DndCharacter } from '../../api/types';
import { C, F } from '../../theme/styleHelpers';

export default function TavernHubScreen() {
  const { data: quota } = useQuotaQuery();
  const { data: characters = [], isLoading: charsLoading } = useListCharactersQuery();
  const { data: classes = [] } = useListClassesQuery();

  const [createCharacter, { isLoading: creating }] = useCreateCharacterMutation();
  const [createSession, { isLoading: starting }] = useCreateSessionMutation();

  const [name, setName] = useState('');
  const [classSlug, setClassSlug] = useState<string | null>(null);

  const forgeHero = async () => {
    if (!name.trim() || !classSlug) return;
    try {
      await createCharacter({ name: name.trim(), class_slug: classSlug }).unwrap();
      setName('');
      setClassSlug(null);
    } catch {
      Alert.alert('Could not forge hero', 'Please try again.');
    }
  };

  const beginTale = async (character: DndCharacter) => {
    try {
      const session = await createSession({
        character_id: character.id,
        mode: 'normal',
        title: `${character.name}'s Tale`,
      }).unwrap();
      router.push(`/tavern/${session.id}` as never);
    } catch {
      Alert.alert('Could not start the tale', 'You may have hit your token quota.');
    }
  };

  const dailyPct = quota
    ? Math.min(100, Math.round((quota.daily_tokens_used / quota.daily_tokens_limit) * 100))
    : 0;

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <ScrollView contentContainerStyle={s.content} showsVerticalScrollIndicator={false}>
        <Text style={s.title}>🐉 Tavern Tales</Text>
        <Text style={s.subtitle}>
          A solo adventure narrated by your AI Dungeon Master.
        </Text>

        {quota && (
          <View style={s.quotaCard}>
            <View style={s.quotaHeader}>
              <Text style={s.quotaLabel}>Daily tokens</Text>
              <Text style={s.quotaValue}>
                {quota.daily_tokens_used.toLocaleString()} /{' '}
                {quota.daily_tokens_limit.toLocaleString()}
              </Text>
            </View>
            <View style={s.quotaTrack}>
              <View style={[s.quotaFill, { width: `${dailyPct}%` }]} />
            </View>
          </View>
        )}

        <Text style={s.sectionTitle}>Your Heroes</Text>
        {charsLoading ? (
          <ActivityIndicator style={{ marginVertical: 16 }} />
        ) : characters.length === 0 ? (
          <Text style={s.muted}>No heroes yet — forge one below to begin.</Text>
        ) : (
          characters.map((ch) => (
            <View key={ch.id} style={s.heroCard}>
              <View style={s.heroAvatar}>
                <Text style={s.heroAvatarText}>{ch.name[0]?.toUpperCase() ?? '?'}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={s.heroName}>{ch.name}</Text>
                <Text style={s.heroMeta}>
                  Lv {ch.level} · {ch.class_slug} · {ch.hp_current}/{ch.hp_max} HP
                </Text>
              </View>
              <TouchableOpacity
                style={s.playBtn}
                onPress={() => beginTale(ch)}
                disabled={starting}
                activeOpacity={0.85}
              >
                <Text style={s.playBtnText}>{starting ? '…' : '▶ Play'}</Text>
              </TouchableOpacity>
            </View>
          ))
        )}

        <Text style={s.sectionTitle}>Forge a Hero</Text>
        <TextInput
          placeholder="Hero name"
          placeholderTextColor={C.textSecondary}
          value={name}
          onChangeText={setName}
          style={s.input}
        />
        <View style={s.classRow}>
          {classes.map((cl) => {
            const active = classSlug === cl.slug;
            return (
              <TouchableOpacity
                key={cl.slug}
                style={[s.classChip, active && s.classChipActive]}
                onPress={() => setClassSlug(cl.slug)}
                activeOpacity={0.85}
              >
                <Text style={[s.classChipText, active && s.classChipTextActive]}>
                  {cl.name}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
        <TouchableOpacity
          style={[s.forgeBtn, (!name.trim() || !classSlug || creating) && s.forgeDisabled]}
          onPress={forgeHero}
          disabled={!name.trim() || !classSlug || creating}
          activeOpacity={0.85}
        >
          {creating ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={s.forgeBtnText}>Forge hero</Text>
          )}
        </TouchableOpacity>

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bgBase },
  content: { paddingHorizontal: 20, paddingTop: 12 },

  title: { fontFamily: F.headingBold, fontSize: 24, color: C.textPrimary },
  subtitle: {
    fontFamily: F.bodyRegular, fontSize: 14, color: C.textSecondary,
    marginTop: 4, marginBottom: 16,
  },

  quotaCard: {
    backgroundColor: C.bgCard, borderRadius: 14, padding: 14,
    borderWidth: 1, borderColor: C.borderDefault, marginBottom: 8,
  },
  quotaHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  quotaLabel: { fontFamily: F.bodySemiBold, fontSize: 13, color: C.textSecondary },
  quotaValue: { fontFamily: F.monoMedium, fontSize: 13, color: C.textPrimary },
  quotaTrack: { height: 6, borderRadius: 3, backgroundColor: C.bgInput, overflow: 'hidden' },
  quotaFill: { height: '100%', borderRadius: 3, backgroundColor: C.brandPrimary },

  sectionTitle: {
    fontFamily: F.headingSemi, fontSize: 17, color: C.textPrimary,
    marginTop: 22, marginBottom: 10,
  },
  muted: { fontFamily: F.bodyRegular, fontSize: 14, color: C.textSecondary },

  heroCard: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    backgroundColor: C.bgCard, borderRadius: 14, padding: 12,
    borderWidth: 1, borderColor: C.borderDefault, marginBottom: 10,
  },
  heroAvatar: {
    width: 48, height: 48, borderRadius: 24,
    backgroundColor: C.brandPrimarySubtle, alignItems: 'center', justifyContent: 'center',
  },
  heroAvatarText: { fontFamily: F.headingBold, fontSize: 20, color: C.brandPrimaryHover },
  heroName: { fontFamily: F.bodyBold, fontSize: 15, color: C.textPrimary },
  heroMeta: { fontFamily: F.bodyRegular, fontSize: 12, color: C.textSecondary, marginTop: 2 },
  playBtn: {
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 999,
    backgroundColor: C.brandPrimary,
  },
  playBtnText: { fontFamily: F.bodyBold, fontSize: 13, color: '#FFFFFF' },

  input: {
    fontFamily: F.bodyRegular, fontSize: 15, color: C.textPrimary,
    backgroundColor: C.bgInput, borderRadius: 12,
    borderWidth: 1, borderColor: C.borderDefault,
    paddingHorizontal: 12, paddingVertical: 12, marginBottom: 10,
  },
  classRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 14 },
  classChip: {
    paddingHorizontal: 12, paddingVertical: 7, borderRadius: 999,
    backgroundColor: C.bgCard, borderWidth: 1, borderColor: C.borderDefault,
  },
  classChipActive: { backgroundColor: C.brandPrimary, borderColor: C.brandPrimary },
  classChipText: { fontFamily: F.bodySemiBold, fontSize: 13, color: C.textSecondary },
  classChipTextActive: { color: '#FFFFFF' },

  forgeBtn: {
    borderRadius: 14, paddingVertical: 15,
    backgroundColor: C.accentGold, alignItems: 'center',
  },
  forgeDisabled: { opacity: 0.5 },
  forgeBtnText: { fontFamily: F.bodyBold, fontSize: 16, color: '#FFFFFF' },
});
