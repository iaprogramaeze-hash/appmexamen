/**
 * Slide-to-confirm button: drag the knob from left to right to trigger
 * the action. Uses the built-in Animated API + PanResponder (no extra deps).
 *
 * PanResponder is created once, so mutable values (maxD, disabled,
 * confirmed) are read through refs to avoid stale closures.
 */
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import React, { useCallback, useRef, useState } from 'react';
import {
  Animated,
  PanResponder,
  StyleSheet,
  Text,
  View,
  ViewStyle,
} from 'react-native';

import { colors, gradientCta, radii } from '../theme';

type ConfirmResult = boolean | void;

type Props = {
  label: string;
  /**
   * Runs when the knob reaches the end. Returning `false` (or throwing) means
   * the action did not succeed, so the knob slides back for another attempt;
   * `void`/`true` keeps the confirmed state as before.
   */
  onConfirm: () => ConfirmResult | Promise<ConfirmResult>;
  disabled?: boolean;
  style?: ViewStyle;
};

const KNOB_SIZE = 52;
const TRACK_HEIGHT = 60;
const PAD = 4;

export function SlideToConfirm({ label, onConfirm, disabled, style }: Props) {
  const [confirmed, setConfirmed] = useState(false);
  const [maxD, setMaxD] = useState(1);
  const dragX = useRef(new Animated.Value(0)).current;

  // Refs so PanResponder callbacks always see fresh values.
  const maxDRef = useRef(1);
  const disabledRef = useRef(!!disabled);
  const confirmedRef = useRef(false);
  const onConfirmRef = useRef(onConfirm);
  const offsetRef = useRef(0);

  disabledRef.current = !!disabled;
  onConfirmRef.current = onConfirm;

  const reset = useCallback(() => {
    offsetRef.current = 0;
    Animated.spring(dragX, {
      toValue: 0,
      useNativeDriver: true,
      bounciness: 8,
    }).start();
  }, [dragX]);

  // A failed action must leave the slider usable again.
  const runConfirm = useCallback(async () => {
    try {
      const result = await onConfirmRef.current();
      if (result === false) {
        confirmedRef.current = false;
        setConfirmed(false);
        reset();
      }
    } catch {
      confirmedRef.current = false;
      setConfirmed(false);
      reset();
    }
  }, [reset]);

  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (_, g) =>
        !disabledRef.current && !confirmedRef.current && Math.abs(g.dx) > 6,
      onPanResponderGrant: () => {
        dragX.setOffset(offsetRef.current);
        dragX.setValue(0);
      },
      onPanResponderMove: (_, g) => {
        const max = maxDRef.current;
        const next = Math.max(0, Math.min(offsetRef.current + g.dx, max));
        dragX.setValue(next - offsetRef.current);
      },
      onPanResponderRelease: () => {
        dragX.flattenOffset();
        const current = (dragX as unknown as { _value: number })._value;
        offsetRef.current = current;
        if (current >= maxDRef.current * 0.85) {
          Animated.timing(dragX, {
            toValue: maxDRef.current,
            duration: 180,
            useNativeDriver: true,
          }).start(() => {
            confirmedRef.current = true;
            setConfirmed(true);
            void runConfirm();
          });
        } else {
          reset();
        }
      },
      onPanResponderTerminate: reset,
    }),
  ).current;

  const handleLayout = useCallback(
    (e: { nativeEvent: { layout: { width: number } } }) => {
      const w = e.nativeEvent.layout.width;
      const max = Math.max(1, w - KNOB_SIZE - PAD * 2);
      maxDRef.current = max;
      setMaxD(max);
    },
    [],
  );

  const inactive = disabled || confirmed;

  return (
    <View
      style={[styles.track, disabled && { opacity: 0.5 }, style]}
      onLayout={handleLayout}
      {...(inactive ? {} : panResponder.panHandlers)}
    >
      {/* Gradient fill that grows with drag (clipped by overflow:hidden) */}
      <Animated.View
        style={[
          styles.fillClip,
          {
            width: dragX.interpolate({
              inputRange: [0, Math.max(1, maxD)],
              outputRange: [0, Math.max(1, maxD)],
              extrapolate: 'clamp',
            }),
          },
        ]}
      >
        <LinearGradient
          colors={[...gradientCta.colors] as [string, string, ...string[]]}
          locations={[...gradientCta.locations]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={styles.fillGradient}
        />
      </Animated.View>

      {/* Label */}
      <View style={styles.labelWrap} pointerEvents="none">
        <Text style={[styles.label, confirmed && { color: '#FFF' }]}>
          {confirmed ? '¡Listo!' : label}
        </Text>
      </View>

      {/* Knob */}
      <Animated.View
        style={[
          styles.knob,
          {
            transform: [
              { translateX: dragX.interpolate({
                  inputRange: [0, Math.max(1, maxD)],
                  outputRange: [PAD, Math.max(1, maxD) + PAD],
                  extrapolate: 'extend',
                }) },
            ],
          },
        ]}
        pointerEvents="none"
      >
        <LinearGradient
          colors={['#FFFFFF', '#E8E0F5']}
          style={styles.knobInner}
        >
          <Ionicons
            name={confirmed ? 'checkmark' : 'arrow-forward'}
            size={24}
            color={confirmed ? '#D14E8A' : '#1B0F29'}
          />
        </LinearGradient>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  track: {
    height: TRACK_HEIGHT,
    borderRadius: radii.pill,
    backgroundColor: colors.surface,
    justifyContent: 'center',
    overflow: 'hidden',
  },
  fillClip: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    overflow: 'hidden',
    borderRadius: radii.pill,
  },
  fillGradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
    borderRadius: radii.pill,
  },
  labelWrap: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
    alignItems: 'center',
    justifyContent: 'center',
  },
  label: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.ink,
    letterSpacing: 0.3,
  },
  knob: {
    position: 'absolute',
    left: 0,
    top: (TRACK_HEIGHT - KNOB_SIZE) / 2,
    width: KNOB_SIZE,
    height: KNOB_SIZE,
    borderRadius: KNOB_SIZE / 2,
  },
  knobInner: {
    flex: 1,
    borderRadius: KNOB_SIZE / 2,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.25,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 3 },
    elevation: 5,
  },
});
