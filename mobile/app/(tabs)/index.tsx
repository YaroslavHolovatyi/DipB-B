/**
 * Search — taverns catalogue with a List / Map toggle.
 *
 * List view: search + price filter + paginated list (tap a row → /bars/[id],
 * heart toggles the favorite).
 *
 * Map view: an OpenStreetMap/Leaflet map inside a WebView (react-native-maps
 * needs a custom dev build and does NOT render in Expo Go SDK 54; Leaflet works
 * over the QR code today). Pins come from the PostGIS `near_*` query, so they
 * are the real "bars near me" set; tapping a pin routes to /bars/[id]. We ask
 * for foreground location and fall back to Lviv's centre if it is denied.
 *
 * The header avatar opens the Profile screen (Profile is no longer a tab).
 */

import { Ionicons } from '@expo/vector-icons';
import { skipToken } from '@reduxjs/toolkit/query';
import * as Location from 'expo-location';
import { router } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { WebView, type WebViewMessageEvent } from 'react-native-webview';

import {
  useFavoriteBarMutation,
  useListBarsQuery,
  useUnfavoriteBarMutation,
} from '../../api/barsApi';
import type { BarSummary, PriceCategory } from '../../api/types';
import { useAppSelector } from '../../store';
import { C, F } from '../../theme/styleHelpers';

const PRICE_OPTIONS: { id: PriceCategory | null; label: string }[] = [
  { id: null, label: 'All' },
  { id: 'budget', label: '$' },
  { id: 'mid', label: '$$' },
  { id: 'premium', label: '$$$' },
  { id: 'luxury', label: '$$$$' },
];

// Lviv centre — fallback when location permission is unavailable.
const FALLBACK: { lat: number; lon: number } = { lat: 49.8397, lon: 24.0297 };
const RADIUS_M = 4000;

type Coords = { lat: number; lon: number };
type ViewMode = 'list' | 'map';

export default function SearchScreen() {
  const [mode, setMode] = useState<ViewMode>('list');
  const user = useAppSelector((s) => s.auth.user);

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <View style={s.headerRow}>
        <View style={s.titleRow}>
          <Ionicons name="shield-half" size={20} color={C.accentGoldText} />
          <Text style={s.title}>Taverns</Text>
        </View>
        <View style={s.headerRight}>
          <View style={s.toggle}>
            <TouchableOpacity
              onPress={() => setMode('list')}
              style={[s.toggleBtn, mode === 'list' && s.toggleBtnActive]}
              activeOpacity={0.85}
            >
              <Text style={[s.toggleText, mode === 'list' && s.toggleTextActive]}>List</Text>
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => setMode('map')}
              style={[s.toggleBtn, mode === 'map' && s.toggleBtnActive]}
              activeOpacity={0.85}
            >
              <Text style={[s.toggleText, mode === 'map' && s.toggleTextActive]}>Map</Text>
            </TouchableOpacity>
          </View>
          <TouchableOpacity
            onPress={() => router.push('/profile' as never)}
            activeOpacity={0.85}
            hitSlop={8}
          >
            <View style={s.avatar}>
              {user?.first_name?.[0] ? (
                <Text style={s.avatarInitial}>
                  {user.first_name[0].toUpperCase()}
                </Text>
              ) : (
                <Ionicons name="person" size={16} color={C.brandPrimaryHover} />
              )}
            </View>
          </TouchableOpacity>
        </View>
      </View>

      {mode === 'list' ? <BarsList /> : <BarsMap />}
    </SafeAreaView>
  );
}

// ── List view ─────────────────────────────────────────────────────────────────
function BarsList() {
  const [search, setSearch] = useState('');
  const [price, setPrice] = useState<PriceCategory | null>(null);
  const [limit, setLimit] = useState(20);

  const params = useMemo(
    () => ({
      q: search.trim() || undefined,
      price_category: price ?? undefined,
      limit,
    }),
    [search, price, limit],
  );

  const { data, isLoading, isFetching, refetch } = useListBarsQuery(params);
  const [favoriteBar] = useFavoriteBarMutation();
  const [unfavoriteBar] = useUnfavoriteBarMutation();

  const onEndReached = useCallback(() => {
    if (!data || data.items.length < data.total) {
      setLimit((l) => Math.min(l + 20, 200));
    }
  }, [data]);

  const renderItem = useCallback(
    ({ item }: { item: BarSummary }) => (
      <BarRow
        item={item}
        onPress={() => router.push(`/bars/${item.id}` as never)}
        onToggleFavorite={() =>
          item.is_favorite ? unfavoriteBar(item.id) : favoriteBar(item.id)
        }
      />
    ),
    [favoriteBar, unfavoriteBar],
  );

  return (
    <>
      <View style={s.searchBox}>
        <Ionicons name="search" size={16} color={C.textSecondary} style={s.searchIcon} />
        <TextInput
          placeholder="Search by name, address…"
          placeholderTextColor={C.textSecondary}
          value={search}
          onChangeText={setSearch}
          style={s.searchInput}
          returnKeyType="search"
          autoCapitalize="none"
        />
      </View>

      <View style={s.chipRow}>
        {PRICE_OPTIONS.map((opt) => {
          const active = price === opt.id;
          return (
            <TouchableOpacity
              key={opt.label}
              onPress={() => setPrice(opt.id)}
              activeOpacity={0.8}
              style={[s.chip, active && s.chipActive]}
            >
              <Text style={[s.chipText, active && s.chipTextActive]}>
                {opt.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {isLoading ? (
        <ActivityIndicator style={{ marginTop: 32 }} />
      ) : (
        <FlatList
          data={data?.items ?? []}
          keyExtractor={(b) => String(b.id)}
          renderItem={renderItem}
          contentContainerStyle={s.listContent}
          onRefresh={refetch}
          refreshing={isFetching && !isLoading}
          onEndReached={onEndReached}
          onEndReachedThreshold={0.4}
          ListEmptyComponent={
            <Text style={s.empty}>No bars match your search.</Text>
          }
          ListFooterComponent={
            data && data.items.length < data.total ? (
              <ActivityIndicator style={{ marginVertical: 12 }} />
            ) : null
          }
        />
      )}
    </>
  );
}

function BarRow({
  item,
  onPress,
  onToggleFavorite,
}: {
  item: BarSummary;
  onPress: () => void;
  onToggleFavorite: () => void;
}) {
  return (
    <TouchableOpacity style={s.row} activeOpacity={0.85} onPress={onPress}>
      <View style={s.thumb}>
        <Text style={s.thumbInitial}>{item.name[0]?.toUpperCase() ?? '?'}</Text>
      </View>
      <View style={{ flex: 1 }}>
        <Text style={s.rowName} numberOfLines={1}>
          {item.name}
        </Text>
        <Text style={s.rowSub} numberOfLines={1}>
          {item.address ?? '—'}
        </Text>
        <View style={s.rowMeta}>
          <View style={s.ratingRow}>
            <Ionicons name="star" size={11} color={C.accentGoldText} />
            <Text style={s.rating}>{Number(item.rating_avg ?? 0).toFixed(1)}</Text>
          </View>
          <Text style={s.dot}>·</Text>
          <Text style={s.price}>
            {item.price_category === 'budget'
              ? '$'
              : item.price_category === 'mid'
              ? '$$'
              : item.price_category === 'premium'
              ? '$$$'
              : '$$$$'}
          </Text>
        </View>
      </View>
      <TouchableOpacity onPress={onToggleFavorite} hitSlop={12} style={s.heart}>
        <Ionicons
          name={item.is_favorite ? 'heart' : 'heart-outline'}
          size={22}
          color={item.is_favorite ? C.error : C.textSecondary}
        />
      </TouchableOpacity>
    </TouchableOpacity>
  );
}

// ── Map view ──────────────────────────────────────────────────────────────────
function buildHtml(center: Coords, bars: BarSummary[]): string {
  const pins = bars
    .filter((b) => b.latitude != null && b.longitude != null)
    .map((b) => ({
      id: b.id,
      lat: b.latitude,
      lng: b.longitude,
      name: b.name,
      address: b.address ?? '',
    }));

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    html, body, #map { height: 100%; margin: 0; padding: 0; background: #0D0D1A; }
    .leaflet-popup-content { font-family: -apple-system, Roboto, sans-serif; }
    .tavern-name { font-weight: 700; font-size: 14px; }
    .tavern-addr { color: #6B7280; font-size: 12px; }
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    var center = ${JSON.stringify([center.lat, center.lon])};
    var pins = ${JSON.stringify(pins)};
    var map = L.map('map', { zoomControl: false, attributionControl: false }).setView(center, 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);

    L.circleMarker(center, {
      radius: 8, color: '#6366F1', weight: 3, fillColor: '#6366F1', fillOpacity: 1,
    }).addTo(map).bindPopup('You are here');

    pins.forEach(function (p) {
      var m = L.marker([p.lat, p.lng]).addTo(map);
      m.bindPopup('<div class="tavern-name">' + p.name + '</div>' +
        (p.address ? '<div class="tavern-addr">' + p.address + '</div>' : ''));
      m.on('click', function () {
        if (window.ReactNativeWebView) {
          window.ReactNativeWebView.postMessage(String(p.id));
        }
      });
    });
  </script>
</body>
</html>`;
}

function BarsMap() {
  const [center, setCenter] = useState<Coords | null>(null);
  const [permissionDenied, setPermissionDenied] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') {
          if (!cancelled) {
            setPermissionDenied(true);
            setCenter(FALLBACK);
          }
          return;
        }
        const pos = await Location.getCurrentPositionAsync({
          accuracy: Location.Accuracy.Balanced,
        });
        if (!cancelled) {
          setCenter({ lat: pos.coords.latitude, lon: pos.coords.longitude });
        }
      } catch {
        if (!cancelled) {
          setPermissionDenied(true);
          setCenter(FALLBACK);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const { data, isLoading } = useListBarsQuery(
    center
      ? { near_lat: center.lat, near_lon: center.lon, radius_m: RADIUS_M, limit: 50 }
      : skipToken,
  );

  const html = useMemo(
    () => (center ? buildHtml(center, data?.items ?? []) : null),
    [center, data],
  );

  const onMessage = (e: WebViewMessageEvent) => {
    const id = Number(e.nativeEvent.data);
    if (!Number.isNaN(id)) router.push(`/bars/${id}` as never);
  };

  return (
    <>
      {permissionDenied && (
        <View style={s.banner}>
          <Text style={s.bannerText}>
            Location off — showing Lviv. Enable location to centre on you.
          </Text>
          <TouchableOpacity
            onPress={() => Location.requestForegroundPermissionsAsync()}
            hitSlop={8}
          >
            <Text style={s.bannerAction}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}

      {!center || !html ? (
        <View style={s.centerFill}>
          <ActivityIndicator />
          <Text style={s.loadingText}>Finding your location…</Text>
        </View>
      ) : (
        <View style={s.mapWrap}>
          <WebView
            originWhitelist={['*']}
            source={{ html }}
            style={s.webview}
            javaScriptEnabled
            domStorageEnabled
            onMessage={onMessage}
          />
          {isLoading && (
            <View style={s.mapLoading} pointerEvents="none">
              <ActivityIndicator />
            </View>
          )}
        </View>
      )}
    </>
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
  headerRight: { flexDirection: 'row', alignItems: 'center', gap: 12 },

  toggle: {
    flexDirection: 'row', backgroundColor: C.bgInput,
    borderRadius: 999, padding: 3, borderWidth: 1, borderColor: C.borderDefault,
  },
  toggleBtn: { paddingHorizontal: 12, paddingVertical: 5, borderRadius: 999 },
  toggleBtnActive: { backgroundColor: C.brandPrimary },
  toggleText: { fontFamily: F.bodySemiBold, fontSize: 12, color: C.textSecondary },
  toggleTextActive: { color: '#FFFFFF' },

  avatar: {
    width: 34, height: 34, borderRadius: 17,
    backgroundColor: C.brandPrimarySubtle, alignItems: 'center', justifyContent: 'center',
    borderWidth: 1, borderColor: C.borderDefault,
  },
  avatarInitial: { fontFamily: F.headingBold, fontSize: 15, color: C.brandPrimaryHover },

  searchBox: {
    flexDirection: 'row', alignItems: 'center',
    marginHorizontal: 20, marginBottom: 10, paddingHorizontal: 12,
    backgroundColor: C.bgInput, borderRadius: 12,
    borderColor: C.borderDefault, borderWidth: 1,
    gap: 8,
  },
  searchIcon: { fontSize: 14 },
  searchInput: {
    flex: 1, fontFamily: F.bodyRegular, color: C.textPrimary,
    fontSize: 15, paddingVertical: 12,
  },

  chipRow: { flexDirection: 'row', gap: 8, paddingHorizontal: 20, marginBottom: 8 },
  chip: {
    borderWidth: 1, borderColor: C.borderDefault,
    paddingHorizontal: 12, paddingVertical: 6,
    borderRadius: 999, backgroundColor: C.bgCard,
  },
  chipActive: { backgroundColor: C.brandPrimary, borderColor: C.brandPrimary },
  chipText: { fontFamily: F.bodySemiBold, fontSize: 13, color: C.textSecondary },
  chipTextActive: { color: '#FFFFFF' },

  listContent: { paddingHorizontal: 20, paddingTop: 4, paddingBottom: 100 },

  row: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: C.borderDefault,
  },
  thumb: {
    width: 56, height: 56, borderRadius: 12,
    backgroundColor: C.accentGoldSubtle, alignItems: 'center', justifyContent: 'center',
  },
  thumbInitial: { fontFamily: F.headingBold, fontSize: 22, color: C.accentGoldText },

  rowName: { fontFamily: F.bodyBold, fontSize: 15, color: C.textPrimary },
  rowSub: { fontFamily: F.bodyRegular, fontSize: 12, color: C.textSecondary, marginTop: 1 },
  rowMeta: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 4 },
  ratingRow: { flexDirection: 'row', alignItems: 'center', gap: 3 },
  rating: { fontFamily: F.bodySemiBold, fontSize: 12, color: C.accentGoldText },
  dot: { color: C.textSecondary },
  price: { fontFamily: F.bodySemiBold, fontSize: 12, color: C.textSecondary },

  heart: { padding: 4 },
  heartIcon: { fontSize: 22 },

  empty: {
    fontFamily: F.bodyRegular, fontSize: 14, color: C.textSecondary,
    textAlign: 'center', paddingTop: 40,
  },

  banner: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    marginHorizontal: 20, marginBottom: 8, paddingHorizontal: 12, paddingVertical: 8,
    backgroundColor: C.accentGoldSubtle, borderRadius: 10,
  },
  bannerText: { flex: 1, fontFamily: F.bodyRegular, fontSize: 12, color: C.accentGoldText },
  bannerAction: { fontFamily: F.bodyBold, fontSize: 12, color: C.accentGoldText },

  centerFill: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 10 },
  loadingText: { fontFamily: F.bodyRegular, fontSize: 13, color: C.textSecondary },

  mapWrap: { flex: 1 },
  webview: { flex: 1, backgroundColor: C.bgBase },
  mapLoading: { position: 'absolute', top: 12, right: 12 },
});
