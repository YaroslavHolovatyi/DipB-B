/**
 * Welcome / Landing Screen
 *
 * The very first screen a new user sees. Designed to be dark and atmospheric —
 * "stepping into a tavern at night" — while clearly communicating what the app
 * is about within the first 10 seconds.
 *
 * Layout (top → bottom):
 *   1. Stars layer — absolute-positioned decorative dots
 *   2. Hero section (flex: 1) — glowing orb, app name, tagline, description
 *   3. CTA section — "Get Started" + "Sign In" + legal text
 */
import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { router } from 'expo-router';

const { width } = Dimensions.get('window');

// ── Decorative stars ─────────────────────────────────────────────────────────
// Fixed layout so the pattern is always the same (no Math.random).
const STARS = [
  { x: 28,  y: 62,  s: 2,   o: 0.35 },
  { x: 75,  y: 38,  s: 3,   o: 0.55 },
  { x: 143, y: 82,  s: 2,   o: 0.40 },
  { x: 198, y: 28,  s: 4,   o: 0.65 },
  { x: 278, y: 58,  s: 2,   o: 0.30 },
  { x: 334, y: 44,  s: 3,   o: 0.50 },
  { x: 52,  y: 132, s: 2,   o: 0.35 },
  { x: 315, y: 115, s: 2,   o: 0.45 },
  { x: 96,  y: 168, s: 3.5, o: 0.60 },
  { x: 252, y: 148, s: 2,   o: 0.38 },
  { x: 36,  y: 225, s: 2,   o: 0.28 },
  { x: 358, y: 198, s: 3,   o: 0.48 },
  { x: 182, y: 210, s: 1.5, o: 0.32 },
  { x: 120, y: 248, s: 2.5, o: 0.42 },
  { x: 305, y: 260, s: 2,   o: 0.36 },
  // Low-density scatter in the lower half
  { x: 62,  y: 320, s: 1.5, o: 0.22 },
  { x: 340, y: 345, s: 2,   o: 0.28 },
  { x: 210, y: 370, s: 1.5, o: 0.20 },
] as const;

// ── Component ─────────────────────────────────────────────────────────────────
export default function WelcomeScreen() {
  return (
    <View style={s.root}>
      <StatusBar style="light" />

      {/* Dark gradient background */}
      <LinearGradient
        colors={['#0A0A1A', '#120E30', '#1E0E3E']}
        style={StyleSheet.absoluteFill}
        start={{ x: 0.3, y: 0 }}
        end={{ x: 0.7, y: 1 }}
      />

      {/* Subtle radial "moon glow" behind the hero orb */}
      <View style={s.moonGlow} pointerEvents="none" />

      {/* Decorative stars */}
      {STARS.map((star, i) => (
        <View
          key={i}
          style={[
            s.star,
            {
              left:    star.x,
              top:     star.y,
              width:   star.s,
              height:  star.s,
              borderRadius: star.s / 2,
              opacity: star.o,
            },
          ]}
          pointerEvents="none"
        />
      ))}

      <SafeAreaView style={s.safeArea}>
        {/* ── HERO SECTION ──────────────────────────────── */}
        <View style={s.hero}>

          {/* Glowing orb — three concentric circles + emoji */}
          <View style={s.orbOuter}>
            <View style={s.orbMid}>
              <View style={s.orbInner}>
                <Text style={s.orbEmoji}>🍺</Text>
              </View>
            </View>
          </View>

          {/* Decorative dice row */}
          <View style={s.diceRow}>
            <Text style={s.diceEmoji}>🎲</Text>
            <View style={s.diceDivider} />
            <Text style={s.diceEmoji}>⚔️</Text>
            <View style={s.diceDivider} />
            <Text style={s.diceEmoji}>🏰</Text>
          </View>

          {/* App name — Fraunces bold in gold */}
          <Text style={s.appName}>Beer &amp; Beverages</Text>

          {/* Tagline — Fraunces semibold in off-white */}
          <Text style={s.tagline}>
            Find Your Tavern.{'\n'}Forge Your Legend.
          </Text>

          {/* Short description */}
          <Text style={s.description}>
            Discover bars, plan raids with friends,{'\n'}
            and let the D20 decide who pays.
          </Text>
        </View>

        {/* ── CTA SECTION ───────────────────────────────── */}
        <View style={s.cta}>

          {/* Primary: Get Started */}
          <TouchableOpacity
            activeOpacity={0.85}
            onPress={() => router.push('/(auth)/sign-up')}
          >
            <LinearGradient
              colors={['#7C3AED', '#6366F1', '#4F46E5']}
              style={s.primaryBtn}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
            >
              <Text style={s.primaryBtnText}>Get Started — It's Free</Text>
            </LinearGradient>
          </TouchableOpacity>

          {/* Secondary: Sign In */}
          <TouchableOpacity
            style={s.secondaryBtn}
            activeOpacity={0.7}
            onPress={() => router.push('/(auth)/sign-in')}
          >
            <Text style={s.secondaryBtnText}>I already have an account</Text>
          </TouchableOpacity>

          {/* Feature chips */}
          <View style={s.chipRow}>
            {['🗺️ Bar finder', '⚔️ Raid planner', '🎲 Bill splitter'].map((chip) => (
              <View key={chip} style={s.chip}>
                <Text style={s.chipText}>{chip}</Text>
              </View>
            ))}
          </View>

          {/* Legal */}
          <Text style={s.legal}>
            By continuing you agree to our{' '}
            <Text style={s.legalLink}>Terms of Service</Text>
            {' '}and{' '}
            <Text style={s.legalLink}>Privacy Policy</Text>
          </Text>
        </View>
      </SafeAreaView>
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#0A0A1A',
  },

  moonGlow: {
    position: 'absolute',
    top:   -80,
    left:  width / 2 - 180,
    width: 360,
    height: 360,
    borderRadius: 180,
    backgroundColor: 'rgba(99, 102, 241, 0.06)',
    ...Platform.select({
      ios: {
        shadowColor:   '#6366F1',
        shadowOffset:  { width: 0, height: 0 },
        shadowOpacity: 0.6,
        shadowRadius:  120,
      },
    }),
  },

  star: {
    position:        'absolute',
    backgroundColor: '#FFFFFF',
  },

  safeArea: {
    flex:              1,
    paddingHorizontal: 24,
    justifyContent:    'space-between',
  },

  // ── Hero ──────────────────────────────────────────────────
  hero: {
    flex:           1,
    alignItems:     'center',
    justifyContent: 'center',
    paddingTop:     12,
    gap:            0,
  },

  orbOuter: {
    width:          180,
    height:         180,
    borderRadius:   90,
    backgroundColor:'rgba(99, 102, 241, 0.06)',
    alignItems:     'center',
    justifyContent: 'center',
    marginBottom:   28,
  },
  orbMid: {
    width:          136,
    height:         136,
    borderRadius:   68,
    backgroundColor:'rgba(99, 102, 241, 0.10)',
    alignItems:     'center',
    justifyContent: 'center',
  },
  orbInner: {
    width:           96,
    height:          96,
    borderRadius:    48,
    backgroundColor: 'rgba(99, 102, 241, 0.18)',
    alignItems:      'center',
    justifyContent:  'center',
    borderWidth:     1,
    borderColor:     'rgba(129, 140, 248, 0.30)',
    // iOS glow
    ...Platform.select({
      ios: {
        shadowColor:   '#6366F1',
        shadowOffset:  { width: 0, height: 0 },
        shadowOpacity: 0.9,
        shadowRadius:  24,
      },
      android: {
        elevation: 16,
      },
    }),
  },
  orbEmoji: {
    fontSize: 44,
  },

  diceRow: {
    flexDirection:  'row',
    alignItems:     'center',
    gap:            8,
    marginBottom:   20,
  },
  diceEmoji: {
    fontSize: 18,
    opacity:  0.75,
  },
  diceDivider: {
    width:           1,
    height:          14,
    backgroundColor: 'rgba(255,255,255,0.15)',
  },

  appName: {
    fontFamily:      'Fraunces_700Bold',
    fontSize:        36,
    color:           '#F59E0B',
    textAlign:       'center',
    letterSpacing:   -0.5,
    marginBottom:    10,
    // Subtle gold text glow on iOS
    ...Platform.select({
      ios: {
        textShadowColor:  'rgba(245, 158, 11, 0.45)',
        textShadowOffset: { width: 0, height: 0 },
        textShadowRadius: 18,
      },
    }),
  },

  tagline: {
    fontFamily:    'Fraunces_600SemiBold',
    fontSize:      26,
    color:         '#F1F5F9',
    textAlign:     'center',
    lineHeight:    34,
    marginBottom:  14,
  },

  description: {
    fontFamily:  'PlusJakartaSans_400Regular',
    fontSize:    15,
    color:       '#94A3B8',
    textAlign:   'center',
    lineHeight:  22,
  },

  // ── CTA ───────────────────────────────────────────────────
  cta: {
    paddingBottom: 8,
    gap:           12,
  },

  primaryBtn: {
    height:         56,
    borderRadius:   16,
    alignItems:     'center',
    justifyContent: 'center',
    // iOS shadow
    ...Platform.select({
      ios: {
        shadowColor:   '#6366F1',
        shadowOffset:  { width: 0, height: 6 },
        shadowOpacity: 0.45,
        shadowRadius:  14,
      },
      android: {
        elevation: 10,
      },
    }),
  },
  primaryBtnText: {
    fontFamily:    'PlusJakartaSans_700Bold',
    fontSize:      17,
    color:         '#FFFFFF',
    letterSpacing: 0.2,
  },

  secondaryBtn: {
    height:         56,
    borderRadius:   16,
    alignItems:     'center',
    justifyContent: 'center',
    borderWidth:    1.5,
    borderColor:    'rgba(255, 255, 255, 0.18)',
    backgroundColor:'rgba(255, 255, 255, 0.04)',
  },
  secondaryBtnText: {
    fontFamily:  'PlusJakartaSans_600SemiBold',
    fontSize:    16,
    color:       '#CBD5E1',
  },

  chipRow: {
    flexDirection:  'row',
    justifyContent: 'center',
    gap:             8,
    flexWrap:       'wrap',
  },
  chip: {
    borderRadius:    999,
    borderWidth:     1,
    borderColor:     'rgba(255,255,255,0.12)',
    backgroundColor: 'rgba(255,255,255,0.05)',
    paddingVertical:  5,
    paddingHorizontal:12,
  },
  chipText: {
    fontFamily: 'PlusJakartaSans_400Regular',
    fontSize:   12,
    color:      '#94A3B8',
  },

  legal: {
    fontFamily: 'PlusJakartaSans_400Regular',
    fontSize:   12,
    color:      '#475569',
    textAlign:  'center',
    marginTop:  2,
    lineHeight: 18,
  },
  legalLink: {
    color: '#818CF8',
  },
});
