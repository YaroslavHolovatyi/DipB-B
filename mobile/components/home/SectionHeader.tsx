import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { C, F } from '../../theme/styleHelpers';

interface Props {
  title: string;
  onSeeAll?: () => void;
}

export function SectionHeader({ title, onSeeAll }: Props) {
  return (
    <View style={s.row}>
      <Text style={s.title}>{title}</Text>
      {onSeeAll && (
        <TouchableOpacity onPress={onSeeAll} activeOpacity={0.7}>
          <Text style={s.seeAll}>See all</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  row: {
    flexDirection:  'row',
    alignItems:     'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop:  20,
    paddingBottom: 12,
  },
  title: {
    fontFamily: F.headingBold,
    fontSize:   18,
    color:      C.textPrimary,
    letterSpacing: -0.3,
  },
  seeAll: {
    fontFamily: F.bodySemiBold,
    fontSize:   13,
    color:      C.brandPrimary,
  },
});
