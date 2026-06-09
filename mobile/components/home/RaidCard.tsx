import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import type { Raid, RsvpStatus } from '../../types/home';
import { C, F } from '../../theme/styleHelpers';

interface Props {
  item: Raid;
  onPress?: (id: string) => void;
}

// ── RSVP pill config ─────────────────────────────────────────────────────────
const RSVP_CONFIG: Record<RsvpStatus, { label: string; bg: string; color: string }> = {
  going:    { label: 'Going',    bg: '#D1FAE5', color: C.success },
  maybe:    { label: 'Maybe',    bg: '#FEF3C7', color: C.warning },
  declined: { label: 'Declined', bg: '#FEE2E2', color: C.error   },
  pending:  { label: 'Pending',  bg: '#E0E7FF', color: C.brandPrimary },
};

export function RaidCard({ item, onPress }: Props) {
  const rsvp = RSVP_CONFIG[item.rsvp];

  return (
    <TouchableOpacity
      style={s.card}
      activeOpacity={0.88}
      onPress={() => onPress?.(item.id)}
    >
      {/* Left — icon box */}
      <View style={s.iconBox}>
        <Text style={s.iconEmoji}>{item.icon}</Text>
      </View>

      {/* Middle — raid info */}
      <View style={s.info}>
        <Text style={s.raidName} numberOfLines={1}>{item.name}</Text>
        <Text style={s.raidWhere} numberOfLines={1}>
          {item.tavernName} · Party of {item.partySize}
        </Text>
      </View>

      {/* Right — time, date, RSVP */}
      <View style={s.right}>
        <Text style={s.time}>{item.time}</Text>
        <Text style={s.date}>{item.date}</Text>
        <View style={[s.rsvpPill, { backgroundColor: rsvp.bg }]}>
          <Text style={[s.rsvpText, { color: rsvp.color }]}>{rsvp.label}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const s = StyleSheet.create({
  card: {
    flexDirection:   'row',
    alignItems:      'center',
    gap:             12,
    backgroundColor: C.bgCard,
    borderRadius:    16,
    padding:         14,
    borderWidth:     1,
    borderColor:     C.borderDefault,
    ...Platform.select({
      ios: {
        shadowColor:   '#000',
        shadowOffset:  { width: 0, height: 2 },
        shadowOpacity: 0.05,
        shadowRadius:  8,
      },
      android: { elevation: 2 },
    }),
  },

  iconBox: {
    width:           44,
    height:          44,
    borderRadius:    12,
    backgroundColor: C.brandPrimarySubtle,
    alignItems:      'center',
    justifyContent:  'center',
    flexShrink:      0,
  },
  iconEmoji: {
    fontSize: 20,
  },

  info: {
    flex:     1,
    minWidth: 0,
  },
  raidName: {
    fontFamily: F.bodyBold,
    fontSize:   14,
    color:      C.textPrimary,
  },
  raidWhere: {
    fontFamily: F.bodyRegular,
    fontSize:   12,
    color:      C.textSecondary,
    marginTop:  2,
  },

  right: {
    alignItems: 'flex-end',
    flexShrink: 0,
  },
  time: {
    fontFamily: F.monoBold,
    fontSize:   13,
    color:      C.brandPrimary,
  },
  date: {
    fontFamily: F.bodyRegular,
    fontSize:   11,
    color:      C.textSecondary,
    marginTop:  2,
  },
  rsvpPill: {
    borderRadius:      999,
    paddingVertical:   3,
    paddingHorizontal: 9,
    marginTop:         5,
  },
  rsvpText: {
    fontFamily: F.bodySemiBold,
    fontSize:   11,
  },
});
