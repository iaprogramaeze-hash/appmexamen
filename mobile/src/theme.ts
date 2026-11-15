/**
 * Visual theme for the mobile app.
 * Dark space theme derived from the reference designs in
 * `imagenes/diseño app/` (dark purple backgrounds, magenta/purple accents,
 * rounded pill inputs, gradient CTAs).
 */
import { Platform, TextStyle, ViewStyle } from 'react-native';

export const colors = {
  // Surfaces
  bg: '#1B0F29', // darkest purple-black screen background
  bgBlue: '#1B1A3B', // dark navy end of the screen gradient
  surface: '#28263B', // card / input surface
  surfaceSoft: '#1B1A3B', // secondary surface
  dark: '#0D0B1A', // floating tab bar / dark badges

  // Text
  ink: '#FFFFFF',
  inkBrown: '#E0DDEB', // secondary text (light lavender)
  muted: '#8B87A3',

  // Brand / accents
  purple: '#BA98F2', // primary accent (light purple)
  purpleDeep: '#9B7BD4', // deeper purple
  periwinkle: '#D14E8A', // pink / magenta accent
  line: '#3A3754', // borders

  // CTA
  peach: '#D14E8A', // primary CTA (magenta)
  peachPressed: '#B83D76', // pressed CTA

  // Feedback
  danger: '#FF6B6B',
  success: '#4ADE80',
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
    shadowColor: '#000000',
    shadowOpacity: 0.3,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 8 },
  },
  android: { elevation: 3 },
  default: {
    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.30)',
  } as unknown as ViewStyle,
});

/** Screen gradient ends (darkest purple → dark navy), as in the shot. */
export const gradient = {
  colors: ['#1B0F29', '#1B1A3B'],
  locations: [0, 1],
} as const;

/** Purple card gradient (level / progress card in the shot). */
export const gradientPurple = {
  colors: ['#BA98F2', '#9B7BD4'],
  locations: [0, 1],
} as const;

/** CTA gradient (magenta → purple → blue), as in the Register button. */
export const gradientCta = {
  colors: ['#D14E8A', '#9B7BD4', '#4A5BC7'],
  locations: [0, 0.5, 1],
} as const;
