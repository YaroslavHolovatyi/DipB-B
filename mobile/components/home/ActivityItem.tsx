import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { ActivityEvent, FantasyRace } from '../../types/home';
import { C, F } from '../../theme/styleHelpers';

interface Props {
  item: ActivityEvent;
  isLast?: boolean;
}

// ── Race avatar colors ────────────────────────────────────────────────────────
const RACE_COLORS: Record<FantasyRace, { bg: string; text: string }> = {
  human:    { bg: C.raceHumanBg,    text: C.raceHumanText    },
  elf:      { bg: C.raceElfBg,      text: C.raceElfText      },
  dwarf:    { bg: C.raceDwarfBg,    text: C.raceDwarfText    },
  orc:      { bg: C.raceOrcBg,      text: C.raceOrcText      },
  halfling: { bg: C.raceHalflingBg, text: C.raceHalflingText },
  gnome:    { bg: C.raceGnomeBg,    text: C.raceGnomeText    },
};

/**
 * Renders activity text with specified substrings bolded.
 * e.g. text = "Sophia checked in at Arcane Alehouse"
 *      boldParts = ["Sophia", "Arcane Alehouse"]
 */
function BoldText({ text, boldParts }: { text: string; boldParts: string[] }) {
  if (!boldParts.length) {
    return <Text style={s.actText}>{text}</Text>;
  }

  // Build a regex that matches any of the bold parts
  const escaped = boldParts.map((p) => p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const regex = new RegExp(`(${escaped.join('|')})`, 'g');
  const parts = text.split(regex);

  return (
    <Text style={s.actText}>
      {parts.map((part, i) =>
        boldParts.includes(part) ? (
          <Text key={i} style={s.actTextBold}>{part}</Text>
        ) : (
          <Text key={i}>{part}</Text>
        )
      )}
    </Text>
  );
}

export function ActivityItem({ item, isLast }: Props) {
  const race = RACE_COLORS[item.actorRace];

  return (
    <View style={[s.row, !isLast && s.rowBorder]}>
      {/* Race-colored avatar */}
      <View style={[s.avatar, { backgroundColor: race.bg }]}>
        <Text style={[s.avatarInitial, { color: race.text }]}>
          {item.actorInitial}
        </Text>
      </View>

      {/* Activity text */}
      <View style={s.textWrap}>
        <BoldText text={item.text} boldParts={item.boldParts} />
      </View>

      {/* Timestamp */}
      <Text style={s.time}>{item.timeAgo}</Text>
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

  avatar: {
    width:          36,
    height:         36,
    borderRadius:   18,
    alignItems:     'center',
    justifyContent: 'center',
    flexShrink:     0,
  },
  avatarInitial: {
    fontFamily: F.bodyBold,
    fontSize:   14,
  },

  textWrap: {
    flex:    1,
    minWidth: 0,
  },
  actText: {
    fontFamily: F.bodyRegular,
    fontSize:   13,
    color:      C.textPrimary,
    lineHeight: 18,
  },
  actTextBold: {
    fontFamily: F.bodyBold,
  },

  time: {
    fontFamily: F.bodyRegular,
    fontSize:   11,
    color:      C.textDisabled,
    flexShrink: 0,
  },
});
