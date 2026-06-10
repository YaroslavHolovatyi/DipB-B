import { Ionicons } from '@expo/vector-icons';
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { C, F } from '../../theme/styleHelpers';

type IoniconName = React.ComponentProps<typeof Ionicons>['name'];

interface BadgeItem {
  id: string;
  name: string;
  state: 'unlocked' | 'rare' | 'locked';
  icon?: IoniconName;
}

interface Props {
  item: BadgeItem;
}

export function AchievementBadge({ item }: Props) {
  const isLocked = item.state === 'locked';
  const tint =
    item.state === 'rare'
      ? C.brandPrimary
      : item.state === 'locked'
        ? C.textDisabled
        : C.accentGoldText;

  return (
    <View style={s.wrap}>
      {/* Icon box */}
      <View style={[s.iconBox, s[item.state]]}>
        <Ionicons name={item.icon ?? 'trophy'} size={24} color={tint} />

        {/* Lock overlay badge */}
        {isLocked && (
          <View style={s.lockBadge}>
            <Ionicons name="lock-closed" size={8} color={C.bgCard} />
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
    backgroundColor: C.brandPrimarySubtle,
    borderWidth:     2,
    borderColor:     C.brandPrimary,
  },
  locked: {
    backgroundColor: C.borderDefault,
    opacity:         0.5,
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
