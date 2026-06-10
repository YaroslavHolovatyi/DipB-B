/**
 * AuthInput — dark-themed text input for auth screens.
 *
 * Features:
 *  • Label always visible above the field (no floating animation for simplicity)
 *  • Focus ring: border changes to brand indigo
 *  • Error state: border + helper text in error red
 *  • Password variant: eye toggle to show/hide
 *  • Fully controlled (value + onChangeText)
 */
import { Ionicons } from '@expo/vector-icons';
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  TextInputProps,
} from 'react-native';
import { F } from '../../theme/styleHelpers';

// ── Dark-mode palette (hardcoded — auth screens are always dark) ──────────────
const DC = {
  bg:             '#1A1A35',
  bgFocus:        '#1E1E3E',
  border:         'rgba(255,255,255,0.12)',
  borderFocus:    '#818CF8',
  borderError:    '#F87171',
  text:           '#F1F5F9',
  placeholder:    '#475569',
  label:          '#94A3B8',
  error:          '#F87171',
  iconTint:       '#64748B',
  iconTintActive: '#818CF8',
};

interface AuthInputProps extends Omit<TextInputProps, 'style'> {
  label: string;
  error?: string;
  isPassword?: boolean;
}

export function AuthInput({
  label,
  error,
  isPassword = false,
  value,
  onChangeText,
  ...rest
}: AuthInputProps) {
  const [focused,     setFocused]     = useState(false);
  const [showSecret,  setShowSecret]  = useState(false);

  const borderColor = error
    ? DC.borderError
    : focused
    ? DC.borderFocus
    : DC.border;

  return (
    <View style={s.wrap}>
      {/* Label */}
      <Text style={[s.label, focused && s.labelFocused]}>{label}</Text>

      {/* Input row */}
      <View style={[s.inputRow, { borderColor, backgroundColor: focused ? DC.bgFocus : DC.bg }]}>
        <TextInput
          style={s.input}
          value={value}
          onChangeText={onChangeText}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholderTextColor={DC.placeholder}
          selectionColor="#818CF8"
          secureTextEntry={isPassword && !showSecret}
          autoCapitalize={isPassword ? 'none' : rest.autoCapitalize}
          autoCorrect={isPassword ? false : rest.autoCorrect}
          {...rest}
        />

        {/* Show/hide toggle for password fields */}
        {isPassword && (
          <TouchableOpacity
            style={s.eyeBtn}
            onPress={() => setShowSecret((v) => !v)}
            activeOpacity={0.7}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            <Ionicons
              name={showSecret ? 'eye' : 'eye-off'}
              size={18}
              color={showSecret ? DC.iconTintActive : DC.iconTint}
            />
          </TouchableOpacity>
        )}
      </View>

      {/* Error helper text */}
      {error ? <Text style={s.errorText}>{error}</Text> : null}
    </View>
  );
}

const s = StyleSheet.create({
  wrap: {
    gap: 6,
  },

  label: {
    fontFamily: F.bodySemiBold,
    fontSize:   13,
    color:      DC.label,
    letterSpacing: 0.2,
  },
  labelFocused: {
    color: DC.iconTintActive,
  },

  inputRow: {
    flexDirection:   'row',
    alignItems:      'center',
    borderWidth:     1.5,
    borderRadius:    14,
    paddingHorizontal: 16,
    height:          52,
  },
  input: {
    flex:       1,
    fontFamily: F.bodyRegular,
    fontSize:   15,
    color:      DC.text,
    // Remove default outline on web
    outlineWidth: 0,
  } as any,

  eyeBtn: {
    paddingLeft: 8,
  },
  eyeIcon: {
    fontSize: 18,
    opacity:  0.5,
  },
  eyeIconActive: {
    opacity: 1,
  },

  errorText: {
    fontFamily: F.bodyRegular,
    fontSize:   12,
    color:      DC.error,
    marginTop:  -2,
  },
});
