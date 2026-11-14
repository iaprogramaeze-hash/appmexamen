/**
 * Visual theme for the mobile app.
 * Palette derived from Dribbble shot 26993647
 * (Kids Learning App UI — Gamified Education & Interactive Lessons).
 */
import { Platform, TextStyle, ViewStyle } from 'react-native';

export const colors = {
  // Surfaces
  bg: '#EDE9F7', // light lavender screen background
  bgBlue: '#E4EAF6', // cool-blue end of the screen gradient
  surface: '#FFFFFF',
  surfaceSoft: '#F7F4FD', // faint lavender card/secondary surface
  dark: '#0A090D', // floating tab bar / dark badges

  // Text
  ink: '#0A090D',
  inkBrown: '#48303B',
  muted: '#9BA2AE',

  // Brand / accents (shot tags)
  purple: '#C9AEFA',
  purpleDeep: '#815680',
  periwinkle: '#B0B8D7',
  line: '#B6C8D3',

  // CTA
  peach: '#F5C99E',
  peachPressed: '#EBB684',

  // Feedback
  danger: '#D93843',
  success: '#2FA76B',
} as const;

export const radii = {
  sm: 12,
  md: 16,
  lg: 24,
  xl: 28,
  pill: 999,
} as const;

export const space = (n: number) => n * 4;

export const fonts = {
  h1: {
    fontSize: 32,
    fontWeight: '800',
    letterSpacing: -0.6,
    color: colors.ink,
  } as TextStyle,
  h2: {
    fontSize: 22,
    fontWeight: '800',
    letterSpacing: -0.3,
    color: colors.ink,
  } as TextStyle,
  h3: {
    fontSize: 17,
    fontWeight: '700',
    color: colors.ink,
  } as TextStyle,
  body: {
    fontSize: 14,
    color: colors.ink,
  } as TextStyle,
  muted: {
    fontSize: 13,
    color: colors.muted,
  } as TextStyle,
  button: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.ink,
  } as TextStyle,
};

/** Soft card elevation, tuned per platform (web falls back to a hairline). */
export const shadow: ViewStyle = Platform.select({
  ios: {
    shadowColor: '#4B3F72',
    shadowOpacity: 0.1,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 8 },
  },
  android: { elevation: 3 },
  default: {
    boxShadow: '0 8px 24px rgba(75, 63, 114, 0.10)',
  } as unknown as ViewStyle,
});

/** Screen gradient ends (lavender → cool blue), as in the shot. */
export const gradient = {
  colors: ['#EDE9F7', '#E4EAF6'],
  locations: [0, 1],
} as const;

/** Purple card gradient (level / progress card in the shot). */
export const gradientPurple = {
  colors: ['#9C8AF0', '#7C6BD1'],
  locations: [0, 1],
} as const;
