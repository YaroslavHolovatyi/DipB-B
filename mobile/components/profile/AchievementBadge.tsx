import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { Achievement } from '../../types/profile';
import { C, F } from '../../theme/styleHelpers';

interface Props {
  item: Achievement;
}

export function AchievementBadge({ item }: Props) {
  const isLocked = item.state === 'locked';

  return (
    <View style={s.wrap}>
      {/* Icon box */}
      <View style={[s.iconBox, s[item.state]]}>
        <Text style={[s.emoji, isLocked && s.emojiLocked]}>{item.emoji}</Text>

        {/* Lock overlay badge */}
        {isLocked && (
          <View style={s.lockBadge}>
            <Text style={s.lockEmoji}>🔒</Text>
          </View>
        )}
      </View>

      {/* Name */}
      <Text
        style={[s.name, isLocked && s.nameLocked]}
        numberOfLines={2}
      >
        {item.name}
      </Text>
    </View>
  );
}

const s = StyleSheet.create({
  wrap: {
    alignItems: 'center',
    gap:        5,
  },

  iconBox: {
    width:          56,
    height:         56,
    borderRadius:   14,
    alignItems:     'center',
    justifyContent: 'center',
    position:       'relative',
  },

  // ── State variants ──────────────────────────────────────────
  unlocked: {
    backgroundColor: C.accentGoldSubtle,
    borderWidth:     2,
    borderColor:     C.accentGold,
  },
  rare: {
    // Indigo gradient approximated with a solid for RN (LinearGradient would need extra import)
    backgroundColor: C.brandPrimarySubtle,
    borderWidth:     2,
    borderColor:     C.brandPrimary,
  },
  locked: {
    backgroundColor: C.borderDefault,
    opacity:         0.5,
  },

  emoji: {
    fontSize: 24,
  },
  emojiLocked: {
    // Already faded by parent opacity
  },

  lockBadge: {
    position:        'absolute',
    bottom:          -4,
    right:           -4,
    width:           18,
    height:          18,
    borderRadius:    9,
    backgroundColor: C.textDisabled,
    alignItems:      'center',
    justifyContent:  'center',
  },
  lockEmoji: {
    fontSize: 8,
  },

  name: {
    fontFamily: F.bodySemiBold,
    fontSize:   10,
    color:      C.textSecondary,
    textAlign:  'center',
    lineHeight: 13,
  },
  nameLocked: {
    color: C.textDisabled,
  },
});
