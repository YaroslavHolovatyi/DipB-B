import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { LeaderboardEntry } from '../../types/profile';
import type { FantasyRace } from '../../types/home';
import { C, F } from '../../theme/styleHelpers';

interface Props {
  entry: LeaderboardEntry;
  isLast?: boolean;
}

// ── Tier rank colors ──────────────────────────────────────────────────────────
function rankColor(rank: number, isCurrentUser?: boolean): string {
  if (isCurrentUser) return C.brandPrimary;
  if (rank === 1) return C.tierGold;
  if (rank === 2) return C.tierSilver;
  if (rank === 3) return C.tierBronze;
  return C.textSecondary;
}

// ── Race avatar colors (same map as ActivityItem) ─────────────────────────────
const RACE_COLORS: Record<FantasyRace, { bg: string; text: string }> = {
  human:    { bg: C.raceHumanBg,    text: C.raceHumanText    },
  elf:      { bg: C.raceElfBg,      text: C.raceElfText      },
  dwarf:    { bg: C.raceDwarfBg,    text: C.raceDwarfText    },
  orc:      { bg: C.raceOrcBg,      text: C.raceOrcText      },
  halfling: { bg: C.raceHalflingBg, text: C.raceHalflingText },
  gnome:    { bg: C.raceGnomeBg,    text: C.raceGnomeText    },
};

export function LeaderboardRow({ entry, isLast }: Props) {
  const race   = RACE_COLORS[entry.race];
  const rColor = rankColor(entry.rank, entry.isCurrentUser);

  return (
    <View
      style={[
        s.row,
        entry.isCurrentUser && s.rowHighlighted,
        !isLast && !entry.isCurrentUser && s.rowBorder,
      ]}
    >
      {/* Rank */}
      <Text style={[s.rank, { color: rColor }]}>{entry.rank}</Text>

      {/* Avatar */}
      <View
        style={[
          s.avatar,
          { backgroundColor: race.bg },
          entry.isCurrentUser && s.avatarHighlighted,
        ]}
      >
        <Text style={[s.avatarInitial, { color: race.text }]}>{entry.initial}</Text>
      </View>

      {/* Name + race */}
      <View style={s.info}>
        <Text style={[s.name, entry.isCurrentUser && s.nameHighlighted]}>
          {entry.name}
        </Text>
        <Text style={s.sub}>{entry.race.charAt(0).toUpperCase() + entry.race.slice(1)} · {entry.city}</Text>
      </View>

      {/* Score */}
      <Text style={[s.score, { color: rColor }]}>
        {entry.score.toLocaleString()}
      </Text>
    </View>
  );
}

const s = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems:    'center',
    gap:           12,
    paddingVertical: 10,
  },
  rowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: C.borderDefault,
  },
  rowHighlighted: {
    backgroundColor: C.brandPrimarySubtle,
    marginHorizontal: -20,
    paddingHorizontal: 20,
    borderRadius:     10,
  },

  rank: {
    fontFamily: F.monoBold,
    fontSize:   16,
    width:      28,
    textAlign:  'center',
    flexShrink: 0,
  },

  avatar: {
    width:          36,
    height:         36,
    borderRadius:   18,
    alignItems:     'center',
    justifyContent: 'center',
    flexShrink:     0,
  },
  avatarHighlighted: {
    borderWidth: 2,
    borderColor: C.brandPrimary,
  },
  avatarInitial: {
    fontFamily: F.bodyBold,
    fontSize:   14,
  },

  info: {
    flex:     1,
    minWidth: 0,
  },
  name: {
    fontFamily: F.bodyBold,
    fontSize:   14,
    color:      C.textPrimary,
  },
  nameHighlighted: {
    color: C.brandPrimary,
  },
  sub: {
    fontFamily: F.bodyRegular,
    fontSize:   11,
    color:      C.textSecondary,
  },

  score: {
    fontFamily: F.monoBold,
    fontSize:   16,
    flexShrink: 0,
  },
});
