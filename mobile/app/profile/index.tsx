/**
 * Profile — wired to real APIs.
 *
 * Reached from the header avatar on the Search / Social tabs (it is no longer a
 * standalone tab). Pulls /auth/me for the user, /achievements/me for badges +
 * points, /checks/_/kind-soul/leaderboard for the kind-soul ranking, and
 * /bars/favorites for the favourite-bars carousel. Includes a Sign Out action
 * that clears the refresh token and bounces back to the welcome screen.
 */

import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import {
  ActivityIndicator,
  Image,
  Platform,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { raceImage } from '../../assets';

import { useLogoutMutation } from '../../api/authApi';
import { useListFavoriteBarsQuery } from '../../api/barsApi';
import { useKindSoulLeaderboardQuery } from '../../api/checksApi';
import {
  useMyAchievementsQuery,
  useMyPointsQuery,
} from '../../api/achievementsApi';
import { useGetRaceQuery } from '../../api/referenceApi';
import { useMyStatsQuery } from '../../api/usersApi';
import { AchievementBadge } from '../../components/profile/AchievementBadge';
import { LeaderboardRow } from '../../components/profile/LeaderboardRow';
import { tokenStorage } from '../../lib/tokenStorage';
import { useAppDispatch, useAppSelector } from '../../store';
import { signedOut } from '../../store/authSlice';
import { C, F } from '../../theme/styleHelpers';

export default function ProfileScreen() {
  const dispatch = useAppDispatch();
  const user = useAppSelector((s) => s.auth.user);
  const refreshToken = useAppSelector((s) => s.auth.refreshToken);

  const { data: race } = useGetRaceQuery(user?.race_id ?? 0, {
    skip: !user?.race_id,
  });
  const { data: achievements = [], isLoading: achLoading } = useMyAchievementsQuery();
  const { data: pointsRes } = useMyPointsQuery();
  const { data: leaderboard = [], isLoading: lbLoading } = useKindSoulLeaderboardQuery(10);
  const { data: favorites = [] } = useListFavoriteBarsQuery();
  const { data: stats } = useMyStatsQuery();
  const [logoutMutation] = useLogoutMutation();

  const handleSignOut = async () => {
    try {
      if (refreshToken) await logoutMutation({ refresh_token: refreshToken }).unwrap();
    } catch {
      /* offline / already invalidated — proceed */
    }
    await tokenStorage.clearRefresh();
    dispatch(signedOut());
  };

  if (!user) {
    return (
      <SafeAreaView style={s.safe}>
        <ActivityIndicator style={{ marginTop: 40 }} />
      </SafeAreaView>
    );
  }

  const myRank = leaderboard.findIndex((r) => r.user_id === user.id);

  return (
    <View style={s.root}>
      <StatusBar barStyle="dark-content" backgroundColor={C.bgBase} />

      <SafeAreaView style={s.safe} edges={['top']}>
        <View style={s.navHeader}>
          <TouchableOpacity onPress={() => router.back()} hitSlop={8} style={s.navBackRow}>
            <Ionicons name="chevron-back" size={18} color={C.textSecondary} />
            <Text style={s.navBack}>Back</Text>
          </TouchableOpacity>
          <Text style={s.navTitle}>Profile</Text>
          <TouchableOpacity onPress={() => router.push('/profile/edit' as never)}>
            <Text style={s.navAction}>Edit</Text>
          </TouchableOpacity>
        </View>

        <ScrollView contentContainerStyle={s.content} showsVerticalScrollIndicator={false}>
          {/* Hero */}
          <LinearGradient
            colors={['#E0E7FF', C.bgBase]}
            style={s.hero}
            start={{ x: 0, y: 0 }}
            end={{ x: 0, y: 1 }}
          >
            <View style={s.avatarWrap}>
              <View style={[s.avatar, { borderColor: race?.primary_color ?? C.brandPrimary }]}>
                {raceImage(race?.slug, user.gender) ? (
                  <Image
                    source={raceImage(race?.slug, user.gender)}
                    style={s.avatarImage}
                    resizeMode="cover"
                  />
                ) : (
                  <Text style={s.avatarInitial}>{user.first_name[0]?.toUpperCase()}</Text>
                )}
              </View>
            </View>
            <Text style={s.displayName}>
              {user.first_name} {user.last_name ?? ''}
            </Text>
            <Text style={s.handle}>@{user.username}</Text>
            {race && (
              <View
                style={[
                  s.racePill,
                  { backgroundColor: (race.primary_color ?? C.brandPrimary) + '22' },
                ]}
              >
                <Text style={[s.raceText, { color: race.primary_color ?? C.brandPrimary }]}>
                  {race.name}
                </Text>
              </View>
            )}
          </LinearGradient>

          {/* Stats */}
          <View style={s.statsRow}>
            <Stat label="Achievements" value={String(achievements.length)} />
            <Stat label="Points" value={String(pointsRes?.points ?? 0)} />
            <Stat label="Favourites" value={String(favorites.length)} />
            <Stat
              label="Kind-soul"
              value={myRank >= 0 ? `#${myRank + 1}` : '—'}
            />
          </View>

          {/* Reputation — live from /users/me/stats */}
          <Section title="Reputation" icon="ribbon">
            <View style={s.repHeader}>
              <View>
                <Text style={s.repRating}>
                  {stats?.social_rating ?? user.social_rating}
                </Text>
                <Text style={s.repRatingLabel}>Social rating</Text>
              </View>
              <View style={s.tierPill}>
                <Text style={s.tierText}>{stats?.rating_tier ?? '—'}</Text>
              </View>
            </View>
            <View style={s.repRow}>
              <Stat
                label="Attended"
                value={String(stats?.events_attended ?? user.events_attended)}
              />
              <Stat
                label="No-shows"
                value={String(stats?.events_ditched ?? user.events_ditched)}
              />
              <Stat
                label="Reliability"
                value={
                  stats?.reliability_pct != null ? `${stats.reliability_pct}%` : '—'
                }
              />
            </View>
            <Text style={s.muted}>
              Show up to events you join — no-shows lower your social rating.
            </Text>
          </Section>

          {/* Achievements */}
          <Section title="Achievements" icon="trophy">
            {achLoading ? (
              <ActivityIndicator />
            ) : achievements.length === 0 ? (
              <Text style={s.muted}>Earn your first by checking in to a tavern.</Text>
            ) : (
              <View style={s.achievementsGrid}>
                {achievements.slice(0, 8).map((ua) => (
                  <AchievementBadge
                    key={ua.achievement.id}
                    item={{
                      id: String(ua.achievement.id),
                      icon: 'trophy',
                      name: ua.achievement.name,
                      state: 'unlocked',
                    }}
                  />
                ))}
              </View>
            )}
          </Section>

          {/* Leaderboard */}
          <Section title="Kind Soul Leaderboard" icon="medal">
            {lbLoading ? (
              <ActivityIndicator />
            ) : leaderboard.length === 0 ? (
              <Text style={s.muted}>No D20 rolls yet.</Text>
            ) : (
              leaderboard.slice(0, 5).map((row, i, arr) => (
                <LeaderboardRow
                  key={row.user_id}
                  entry={{
                    rank: i + 1,
                    initial: row.first_name[0]?.toUpperCase() ?? 'B',
                    name: row.first_name,
                    race: 'human',
                    city: '',
                    score: Number(row.total_paid_for_others),
                    isCurrentUser: row.user_id === user.id,
                  }}
                  isLast={i === arr.length - 1}
                />
              ))
            )}
          </Section>

          {/* Favourites */}
          {favorites.length > 0 && (
            <Section title="Favourite Taverns" icon="heart">
              <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                <View style={s.favRow}>
                  {favorites.map((b) => (
                    <TouchableOpacity
                      key={b.id}
                      style={s.favCard}
                      activeOpacity={0.85}
                      onPress={() => router.push(`/bars/${b.id}` as never)}
                    >
                      <View style={s.favThumb}>
                        <Text style={s.favInitial}>{b.name[0]?.toUpperCase()}</Text>
                      </View>
                      <Text style={s.favName} numberOfLines={1}>
                        {b.name}
                      </Text>
                      <View style={s.favSubRow}>
                        <Ionicons name="star" size={11} color={C.accentGold} />
                        <Text style={s.favSub}>{Number(b.rating_avg).toFixed(1)}</Text>
                      </View>
                    </TouchableOpacity>
                  ))}
                </View>
              </ScrollView>
            </Section>
          )}

          <TouchableOpacity
            style={s.retakeBtn}
            activeOpacity={0.85}
            onPress={() => router.push('/quiz?retake=1' as never)}
          >
            <Ionicons name="dice" size={16} color={C.brandPrimaryHover} />
            <Text style={s.retakeText}>Retake race quiz</Text>
          </TouchableOpacity>

          <TouchableOpacity style={s.signOut} activeOpacity={0.85} onPress={handleSignOut}>
            <Text style={s.signOutText}>Sign Out</Text>
          </TouchableOpacity>

          <View style={{ height: 40 }} />
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <View style={s.stat}>
      <Text style={s.statValue}>{value}</Text>
      <Text style={s.statLabel}>{label}</Text>
    </View>
  );
}

function Section({
  title,
  icon,
  children,
}: {
  title: string;
  icon?: React.ComponentProps<typeof Ionicons>['name'];
  children: React.ReactNode;
}) {
  return (
    <View style={s.section}>
      <View style={s.sectionTitleRow}>
        {icon && <Ionicons name={icon} size={16} color={C.brandPrimary} />}
        <Text style={s.sectionTitle}>{title}</Text>
      </View>
      {children}
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bgBase },
  safe: { flex: 1 },

  navHeader: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 20, paddingTop: 8, paddingBottom: 8,
  },
  navBackRow: { flexDirection: 'row', alignItems: 'center', gap: 2 },
  navBack: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.textSecondary },
  navTitle: { fontFamily: F.headingBold, fontSize: 22, color: C.textPrimary },
  navAction: { fontFamily: F.bodySemiBold, fontSize: 14, color: C.brandPrimary },

  content: { paddingBottom: 80 },

  hero: { alignItems: 'center', paddingVertical: 24, paddingHorizontal: 20, gap: 6 },
  avatarWrap: { marginBottom: 8 },
  avatar: {
    width: 90, height: 90, borderRadius: 45, borderWidth: 3,
    backgroundColor: '#FFFFFF', alignItems: 'center', justifyContent: 'center',
  },
  avatarImage: { width: '100%', height: '100%', borderRadius: 45 },
  avatarInitial: { fontFamily: F.headingBold, fontSize: 36, color: C.textPrimary },
  displayName: { fontFamily: F.headingBold, fontSize: 22, color: C.textPrimary },
  handle: { fontFamily: F.bodyRegular, fontSize: 13, color: C.textSecondary },
  racePill: { paddingHorizontal: 14, paddingVertical: 6, borderRadius: 999, marginTop: 6 },
  raceText: { fontFamily: F.bodyBold, fontSize: 12, letterSpacing: 0.4, textTransform: 'uppercase' },

  statsRow: {
    flexDirection: 'row', justifyContent: 'space-around',
    paddingHorizontal: 20, paddingVertical: 16, gap: 8,
    backgroundColor: C.bgCard, marginHorizontal: 16, borderRadius: 16,
    marginTop: -16,
    ...Platform.select({
      ios: { shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 10 },
      android: { elevation: 3 },
    }),
  },
  stat: { alignItems: 'center', flex: 1 },
  statValue: { fontFamily: F.headingBold, fontSize: 18, color: C.textPrimary },
  statLabel: { fontFamily: F.bodyRegular, fontSize: 11, color: C.textSecondary, marginTop: 2 },

  repHeader: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 14, marginBottom: 10,
    backgroundColor: C.brandPrimarySubtle, borderRadius: 16,
  },
  repRating: { fontFamily: F.headingBold, fontSize: 30, color: C.brandPrimaryHover },
  repRatingLabel: { fontFamily: F.bodyRegular, fontSize: 12, color: C.textSecondary, marginTop: 2 },
  tierPill: {
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 999,
    backgroundColor: C.bgCard, borderWidth: 1, borderColor: C.brandPrimary,
  },
  tierText: { fontFamily: F.bodyBold, fontSize: 13, color: C.brandPrimaryHover },

  repRow: {
    flexDirection: 'row', justifyContent: 'space-around',
    paddingVertical: 14, gap: 8,
    backgroundColor: C.bgCard, borderRadius: 16,
    borderWidth: 1, borderColor: C.borderDefault, marginBottom: 10,
  },

  section: { paddingHorizontal: 20, marginTop: 24 },
  sectionTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 12 },
  sectionTitle: {
    fontFamily: F.headingSemi, fontSize: 16, color: C.textPrimary,
  },
  muted: { fontFamily: F.bodyRegular, fontSize: 13, color: C.textSecondary },

  achievementsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },

  favRow: { flexDirection: 'row', gap: 12 },
  favCard: {
    width: 120, backgroundColor: C.bgCard, borderColor: C.borderDefault, borderWidth: 1,
    borderRadius: 12, padding: 10, alignItems: 'center', gap: 8,
  },
  favThumb: {
    width: 60, height: 60, borderRadius: 10,
    backgroundColor: C.accentGoldSubtle, alignItems: 'center', justifyContent: 'center',
  },
  favInitial: { fontFamily: F.headingBold, fontSize: 24, color: C.accentGoldText },
  favName: { fontFamily: F.bodyBold, fontSize: 13, color: C.textPrimary, textAlign: 'center' },
  favSubRow: { flexDirection: 'row', alignItems: 'center', gap: 3 },
  favSub: { fontFamily: F.bodyRegular, fontSize: 11, color: C.textSecondary },

  retakeBtn: {
    marginHorizontal: 20, marginTop: 28,
    backgroundColor: C.brandPrimarySubtle, paddingVertical: 14, borderRadius: 12,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
  },
  retakeText: { fontFamily: F.bodyBold, fontSize: 15, color: C.brandPrimaryHover },

  signOut: {
    marginHorizontal: 20, marginTop: 12,
    backgroundColor: C.errorSubtle, paddingVertical: 14, borderRadius: 12,
    alignItems: 'center',
  },
  signOutText: { fontFamily: F.bodyBold, fontSize: 15, color: C.error },
});
