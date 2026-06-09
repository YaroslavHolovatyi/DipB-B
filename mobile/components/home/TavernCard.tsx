import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import type { Tavern } from '../../types/home';
import { C, F } from '../../theme/styleHelpers';

interface Props {
  item: Tavern;
  onPress?: (id: string) => void;
}

export function TavernCard({ item, onPress }: Props) {
  return (
    <TouchableOpacity
      style={s.card}
      activeOpacity={0.88}
      onPress={() => onPress?.(item.id)}
    >
      {/* Image area — gradient placeholder */}
      <View style={s.imageArea}>
        <LinearGradient
          colors={item.gradientColors}
          style={StyleSheet.absoluteFill}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        />
        {/* Bottom gradient overlay */}
        <LinearGradient
          colors={['transparent', 'rgba(0,0,0,0.38)']}
          style={StyleSheet.absoluteFill}
          start={{ x: 0, y: 0.4 }}
          end={{ x: 0, y: 1 }}
        />
        {/* Rating chip */}
        <View style={s.ratingChip}>
          <Text style={s.ratingStar}>★</Text>
          <Text style={s.ratingText}>{item.rating.toFixed(1)}</Text>
        </View>
      </View>

      {/* Card body */}
      <View style={s.body}>
        <Text style={s.name} numberOfLines={1}>{item.name}</Text>
        <View style={s.meta}>
          <View style={s.vibeChip}>
            <Text style={s.vibeText}>{item.vibe}</Text>
          </View>
          <Text style={s.distance}>
            {item.distanceKm < 1
              ? `${(item.distanceKm * 1000).toFixed(0)}m`
              : `${item.distanceKm.toFixed(1)} km`}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const s = StyleSheet.create({
  card: {
    width:        200,
    borderRadius: 16,
    backgroundColor: C.bgCard,
    overflow:     'hidden',
    borderWidth:  1,
    borderColor:  C.borderDefault,
    ...Platform.select({
      ios: {
        shadowColor:   '#000',
        shadowOffset:  { width: 0, height: 2 },
        shadowOpacity: 0.07,
        shadowRadius:  10,
      },
      android: { elevation: 3 },
    }),
  },

  imageArea: {
    height:   110,
    overflow: 'hidden',
  },

  ratingChip: {
    position:        'absolute',
    top:             8,
    right:           8,
    flexDirection:   'row',
    alignItems:      'center',
    gap:             3,
    backgroundColor: 'rgba(0,0,0,0.52)',
    borderRadius:    8,
    paddingVertical: 3,
    paddingHorizontal: 8,
  },
  ratingStar: {
    color:    C.accentGold,
    fontSize: 11,
  },
  ratingText: {
    fontFamily: F.monoBold,
    fontSize:   11,
    color:      '#FFFFFF',
  },

  body: {
    paddingHorizontal: 12,
    paddingTop:        10,
    paddingBottom:     12,
  },
  name: {
    fontFamily:   F.headingSemi,
    fontSize:     14,
    color:        C.textPrimary,
    marginBottom: 4,
  },
  meta: {
    flexDirection: 'row',
    alignItems:    'center',
    gap:           6,
  },
  vibeChip: {
    borderRadius:      999,
    borderWidth:       1,
    borderColor:       C.borderDefault,
    backgroundColor:   C.bgBase,
    paddingVertical:   2,
    paddingHorizontal: 8,
  },
  vibeText: {
    fontFamily: F.bodySemiBold,
    fontSize:   11,
    color:      C.textSecondary,
  },
  distance: {
    fontFamily: F.monoMedium,
    fontSize:   11,
    color:      C.textSecondary,
  },
});
