/**
 * Glossy sphere bubble for the Inicio hub (S14, reference
 * `imagenes/diseño app/3.jpg`): a big 3D-looking ball with the label in the
 * middle, an idle floating bob ("movimiento de burbuja", L40) and a press
 * animation (scale down + spring back, native driver).
 */
import { LinearGradient } from 'expo-linear-gradient';
import React, { useEffect, useRef } from 'react';
import { Animated, Easing, Pressable, StyleSheet, Text, View } from 'react-native';

import { colors, radii, space } from '../theme';

type Props = {
  /** White label shown in the middle of the sphere. */
  label: string;
  /** `[start, end]` gradient of the sphere surface. */
  sphereColors: [string, string];
  onPress: () => void;
  /** Diameter in dp (reference spheres are ~200). */
  size?: number;
  /** Delay before the idle float loop starts (ms) — staggers bubbles. */
  floatDelay?: number;
};

export function SectorBubble({
  label,
  sphereColors,
  onPress,
  size = 196,
  floatDelay = 0,
}: Props) {
  const scale = useRef(new Animated.Value(1)).current;
  const float = useRef(new Animated.Value(0)).current;
  const radius = size / 2;

  // Idle bubble movement: gentle up-and-down bob, staggered per bubble.
  useEffect(() => {
    const bob = Animated.loop(
      Animated.sequence([
        Animated.timing(float, {
          toValue: -10,
          duration: 1900,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
        Animated.timing(float, {
          toValue: 0,
          duration: 1900,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
      ]),
    );
    const timer = setTimeout(() => bob.start(), floatDelay);
    return () => {
      clearTimeout(timer);
      bob.stop();
    };
  }, [float, floatDelay]);

  const pressIn = () => {
    Animated.spring(scale, {
      toValue: 0.92,
      useNativeDriver: true,
      speed: 40,
      bounciness: 4,
    }).start();
  };

  const pressOut = () => {
    Animated.spring(scale, {
      toValue: 1,
      useNativeDriver: true,
      speed: 16,
      bounciness: 14,
    }).start();
  };

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      onPress={onPress}
      onPressIn={pressIn}
      onPressOut={pressOut}
      style={{ width: size, height: size }}
    >
      <Animated.View
        style={[
          styles.glow,
          {
            width: size,
            height: size,
            borderRadius: radius,
            transform: [{ translateY: float }, { scale }],
            shadowColor: sphereColors[0],
          },
        ]}
      >
        <View style={[styles.sphere, { width: size, height: size, borderRadius: radius }]}>
          <LinearGradient
            colors={sphereColors}
            start={{ x: 0.1, y: 0 }}
            end={{ x: 0.9, y: 1 }}
            style={[StyleSheet.absoluteFill, { borderRadius: radius }]}
          />
          {/* Bottom shade for the 3D sphere depth. */}
          <LinearGradient
            colors={['transparent', 'rgba(0,0,0,0.38)']}
            style={[StyleSheet.absoluteFill, { borderRadius: radius }]}
          />
          {/* Gloss highlight (top-left), as in the reference shot. */}
          <View
            pointerEvents="none"
            style={[
              styles.gloss,
              { width: size * 0.5, height: size * 0.24, borderRadius: radii.pill },
            ]}
          />
          <Text numberOfLines={2} style={styles.label}>
            {label}
          </Text>
        </View>
      </Animated.View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  glow: {
    elevation: 10,
    shadowOpacity: 0.5,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 12 },
  },
  sphere: {
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    backgroundColor: colors.surface,
  },
  gloss: {
    position: 'absolute',
    top: '9%',
    left: '14%',
    backgroundColor: 'rgba(255,255,255,0.28)',
    transform: [{ rotate: '-18deg' }],
  },
  label: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: '800',
    textAlign: 'center',
    paddingHorizontal: space(4),
    textShadowColor: 'rgba(0,0,0,0.45)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 4,
  },
});
