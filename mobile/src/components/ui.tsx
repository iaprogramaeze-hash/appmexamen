/**
 * Shared UI primitives matching the gamified kids-app visual language:
 * lavender gradient screens, white rounded cards, peach pill CTAs,
 * dark circular arrow badges, chips and progress bars.
 */
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import React, { useState } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  TextInputProps,
  View,
  ViewStyle,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors, fonts, gradient, radii, shadow, space } from '../theme';

/** Full-screen lavender gradient with safe areas. */
export function Screen({
  children,
  edges = ['top'],
}: {
  children: React.ReactNode;
  edges?: ('top' | 'bottom')[];
}) {
  return (
    <LinearGradient
      colors={[...gradient.colors] as [string, string, ...string[]]}
      locations={[...gradient.locations]}
      style={styles.flex}
    >
      <SafeAreaView style={styles.flex} edges={edges}>
        {children}
      </SafeAreaView>
    </LinearGradient>
  );
}

/** White rounded card. */
export function Card({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: ViewStyle | ViewStyle[];
}) {
  return <View style={[styles.card, shadow, style]}>{children}</View>;
}

type PillVariant = 'primary' | 'dark' | 'ghost' | 'subtle';

/** Pill button; `primary` is the peach CTA with the dark arrow badge. */
export function PillButton({
  label,
  onPress,
  variant = 'primary',
  withArrow = false,
  disabled = false,
  style,
}: {
  label: string;
  onPress?: () => void;
  variant?: PillVariant;
  withArrow?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
}) {
  const isPeach = variant === 'primary';
  const bg: ViewStyle =
    variant === 'primary'
      ? { backgroundColor: colors.peach }
      : variant === 'dark'
        ? { backgroundColor: colors.dark }
        : variant === 'ghost'
          ? {
              backgroundColor: colors.surface,
              borderWidth: 1,
              borderColor: colors.periwinkle,
            }
          : { backgroundColor: 'transparent' };

  const textColor =
    variant === 'dark'
      ? '#FFFFFF'
      : variant === 'subtle'
        ? colors.muted
        : colors.ink;

  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.pill,
        bg,
        isPeach && !pressed && shadow,
        pressed && { opacity: 0.85, transform: [{ scale: 0.99 }] },
        disabled && { opacity: 0.5 },
        style,
      ]}
    >
      <Text style={[fonts.button, { color: textColor }]}>{label}</Text>
      {withArrow && (
        <View style={styles.arrowBadge}>
          <Ionicons name="arrow-up" size={14} color="#FFFFFF" />
        </View>
      )}
    </Pressable>
  );
}

/** Label + rounded white input with optional leading icon. */
export function Field({
  label,
  icon,
  ...props
}: TextInputProps & { label: string; icon?: keyof typeof Ionicons.glyphMap }) {
  const [focused, setFocused] = useState(false);
  return (
    <View style={{ gap: space(1.5) }}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View
        style={[
          styles.fieldBox,
          focused && { borderColor: colors.purpleDeep, borderWidth: 1.5 },
        ]}
      >
        {icon && (
          <Ionicons name={icon} size={18} color={colors.muted} />
        )}
        <TextInput
          placeholderTextColor={colors.muted}
          {...props}
          onFocus={(e) => {
            setFocused(true);
            props.onFocus?.(e);
          }}
          onBlur={(e) => {
            setFocused(false);
            props.onBlur?.(e);
          }}
          style={styles.fieldInput}
        />
      </View>
    </View>
  );
}

/** Selectable pill chip (filter row). */
export function Chip({
  label,
  active = false,
  onPress,
}: {
  label: string;
  active?: boolean;
  onPress?: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={[styles.chip, active && { backgroundColor: colors.dark, borderColor: colors.dark }]}
    >
      <Text
        style={[
          styles.chipText,
          active && { color: '#FFFFFF', fontWeight: '700' },
        ]}
      >
        {label}
      </Text>
    </Pressable>
  );
}

/** Thin progress bar: track + fill (peach), as in the level card. */
export function ProgressBar({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(1, value));
  return (
    <View style={styles.track}>
      <View style={[styles.fill, { width: `${pct * 100}%` }]} />
    </View>
  );
}

/** Dark circular badge with an up-right arrow (card corner action). */
export function ArrowCircle({ onPress }: { onPress?: () => void }) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [styles.arrowCircle, pressed && { opacity: 0.8 }]}
    >
      <Ionicons name="arrow-up" size={16} color="#FFFFFF" />
    </Pressable>
  );
}

/** Small dark count badge (e.g. "0/5"). */
export function CountBadge({ label }: { label: string }) {
  return (
    <View style={styles.countBadge}>
      <Text style={styles.countBadgeText}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    padding: space(5),
    gap: space(3),
  },
  pill: {
    minHeight: 52,
    borderRadius: radii.pill,
    paddingHorizontal: space(6),
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: space(2),
  },
  arrowBadge: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: colors.dark,
    alignItems: 'center',
    justifyContent: 'center',
    transform: [{ rotate: '45deg' }],
  },
  fieldLabel: {
    ...fonts.body,
    fontWeight: '600',
    fontSize: 13,
  },
  fieldBox: {
    backgroundColor: colors.surface,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: 'rgba(176, 184, 215, 0.5)',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: space(4),
    minHeight: 50,
    gap: space(2),
  },
  fieldInput: {
    flex: 1,
    fontSize: 15,
    color: colors.ink,
    paddingVertical: space(3),
  },
  chip: {
    paddingHorizontal: space(4.5),
    paddingVertical: space(2.5),
    borderRadius: radii.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.periwinkle,
  },
  chipText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.ink,
  },
  track: {
    height: 10,
    borderRadius: radii.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.35)',
    overflow: 'hidden',
  },
  fill: {
    height: '100%',
    borderRadius: radii.pill,
    backgroundColor: colors.peach,
  },
  arrowCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.dark,
    alignItems: 'center',
    justifyContent: 'center',
  },
  countBadge: {
    minWidth: 42,
    height: 42,
    paddingHorizontal: space(2),
    borderRadius: 21,
    backgroundColor: colors.dark,
    alignItems: 'center',
    justifyContent: 'center',
  },
  countBadgeText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
});
