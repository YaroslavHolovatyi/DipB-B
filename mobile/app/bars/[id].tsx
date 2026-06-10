/**
 * Bar detail — hero image, info, reviews, favorite toggle.
 *
 * Linked from the home feed and the bars catalogue. Includes a "Start a raid
 * here" button that deep-links into the raid-creation modal pre-filled with
 * this bar's id.
 */

import { Ionicons } from '@expo/vector-icons';
import React from 'react';
import { router, useLocalSearchParams } from 'expo-router';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  useFavoriteBarMutation,
  useGetBarQuery,
  useUnfavoriteBarMutation,
} from '../../api/barsApi';
import { C, F } from '../../theme/styleHelpers';

export default function BarDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const barId = Number(id);
  const { data: bar, isLoading } = useGetBarQuery(barId, { skip: !barId });
  const [favoriteBar] = useFavoriteBarMutation();
  const [unfavoriteBar] = useUnfavoriteBarMutation();

  if (isLoading || !bar) {
    return (
      <SafeAreaView style={s.safe}>
        <ActivityIndicator style={{ marginTop: 40 }} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <ScrollView contentContainerStyle={s.content}>
        <TouchableOpacity style={s.back} onPress={() => router.back()}>
          <Ionicons name="chevron-back" size={18} color={C.textSecondary} />
          <Text style={s.backText}>Back</Text>
        </TouchableOpacity>

        <View style={s.hero}>
          <Text style={s.heroInitial}>{bar.name[0]?.toUpperCase()}</Text>
        </View>

        <View style={s.titleRow}>
          <View style={{ flex: 1 }}>
            <Text style={s.title}>{bar.name}</Text>
            <Text style={s.address}>{bar.address ?? 'Address unknown'}</Text>
          </View>
          <TouchableOpacity
            onPress={() =>
              bar.is_favorite ? unfavoriteBar(barId) : favoriteBar(barId)
            }
            style={s.heart}
            hitSlop={12}
          >
            <Ionicons
              name={bar.is_favorite ? 'heart' : 'heart-outline'}
              size={26}
              color={bar.is_favorite ? C.error : C.textSecondary}
            />
          </TouchableOpacity>
        </View>

        <View style={s.metaRow}>
          <MetaPill icon="star" label={bar.rating_avg.toFixed(1)} sub={`${bar.rating_count} reviews`} />
          <MetaPill
            label={
              bar.price_category === 'budget'
                ? '$'
                : bar.price_category === 'mid'
                ? '$$'
                : bar.price_category === 'premium'
                ? '$$$'
                : '$$$$'
            }
            sub="Price"
          />
          {bar.distance_m != null && (
            <MetaPill
              label={
                bar.distance_m < 1000
                  ? `${bar.distance_m.toFixed(0)} m`
                  : `${(bar.distance_m / 1000).toFixed(1)} km`
              }
              sub="From you"
            />
          )}
        </View>

        {bar.description && <Text style={s.body}>{bar.description}</Text>}

        {bar.vibes.length > 0 && (
          <>
            <Text style={s.sectionTitle}>Vibes</Text>
            <View style={s.vibeRow}>
              {bar.vibes.map((v) => (
                <View key={v.id} style={s.vibe}>
                  <Text style={s.vibeText}>{v.name}</Text>
                </View>
              ))}
            </View>
          </>
        )}

        <Text style={s.sectionTitle}>Recent reviews</Text>
        {bar.recent_reviews.length === 0 ? (
          <Text style={s.muted}>No reviews yet — be the first.</Text>
        ) : (
          bar.recent_reviews.map((r) => (
            <View key={r.id} style={s.reviewCard}>
              <View style={s.reviewRating}>
                {Array.from({ length: r.rating }).map((_, i) => (
                  <Ionicons key={i} name="star" size={13} color={C.accentGoldText} />
                ))}
              </View>
              {r.text && <Text style={s.reviewText}>{r.text}</Text>}
              <Text style={s.muted}>{new Date(r.created_at).toLocaleDateString()}</Text>
            </View>
          ))
        )}

        <TouchableOpacity
          style={s.cta}
          activeOpacity={0.85}
          onPress={() =>
            router.push(`/raids/new?barId=${barId}` as never)
          }
        >
          <Ionicons name="flag" size={16} color="#FFFFFF" />
          <Text style={s.ctaText}>Start a raid here</Text>
        </TouchableOpacity>

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

function MetaPill({
  label,
  sub,
  icon,
}: {
  label: string;
  sub: string;
  icon?: React.ComponentProps<typeof Ionicons>['name'];
}) {
  return (
    <View style={s.meta}>
      <View style={s.metaLabelRow}>
        {icon && <Ionicons name={icon} size={13} color={C.accentGoldText} />}
        <Text style={s.metaLabel}>{label}</Text>
      </View>
      <Text style={s.metaSub}>{sub}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bgBase },
  content: { paddingHorizontal: 20, paddingTop: 8, paddingBottom: 40 },

  back: { flexDirection: 'row', alignItems: 'center', gap: 2, paddingVertical: 8 },
  backText: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.textSecondary },

  hero: {
    height: 180, borderRadius: 20, marginTop: 8,
    backgroundColor: C.accentGoldSubtle,
    alignItems: 'center', justifyContent: 'center',
  },
  heroInitial: { fontFamily: F.headingBold, fontSize: 96, color: C.accentGoldText },

  titleRow: { flexDirection: 'row', alignItems: 'flex-start', marginTop: 16, gap: 8 },
  title: { fontFamily: F.headingBold, fontSize: 26, color: C.textPrimary },
  address: { fontFamily: F.bodyRegular, fontSize: 13, color: C.textSecondary, marginTop: 4 },

  heart: { padding: 6 },
  heartIcon: { fontSize: 26 },

  metaRow: { flexDirection: 'row', gap: 8, marginTop: 16 },
  meta: {
    flex: 1, alignItems: 'center', paddingVertical: 10,
    backgroundColor: C.bgCard, borderColor: C.borderDefault, borderWidth: 1, borderRadius: 12,
  },
  metaLabelRow: { flexDirection: 'row', alignItems: 'center', gap: 3 },
  metaLabel: { fontFamily: F.bodyBold, fontSize: 15, color: C.textPrimary },
  metaSub: { fontFamily: F.bodyRegular, fontSize: 11, color: C.textSecondary, marginTop: 2 },

  body: {
    fontFamily: F.bodyRegular, fontSize: 14, color: C.textPrimary,
    marginTop: 18, lineHeight: 21,
  },

  sectionTitle: {
    fontFamily: F.headingSemi, fontSize: 16, color: C.textPrimary,
    marginTop: 22, marginBottom: 8,
  },
  vibeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  vibe: {
    backgroundColor: C.brandPrimarySubtle, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 999,
  },
  vibeText: { fontFamily: F.bodySemiBold, fontSize: 12, color: C.brandPrimaryHover },

  reviewCard: {
    backgroundColor: C.bgCard, borderColor: C.borderDefault, borderWidth: 1,
    borderRadius: 12, padding: 12, marginBottom: 10,
  },
  reviewRating: { flexDirection: 'row', gap: 1, marginBottom: 4 },
  reviewText: { fontFamily: F.bodyRegular, fontSize: 14, color: C.textPrimary, marginBottom: 6 },

  muted: { fontFamily: F.bodyRegular, fontSize: 12, color: C.textSecondary },

  cta: {
    backgroundColor: C.brandPrimary, borderRadius: 14, flexDirection: 'row', gap: 8,
    paddingVertical: 14, alignItems: 'center', justifyContent: 'center', marginTop: 24,
  },
  ctaText: { fontFamily: F.bodyBold, fontSize: 15, color: '#FFFFFF' },
});
