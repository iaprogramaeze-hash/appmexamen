/**
 * Student tabs: Inicio · Permisos · Notas · Perfil.
 * Floating dark pill tab bar (reference shot), active icon on a peach circle.
 */
import { Ionicons } from '@expo/vector-icons';
import { Tabs } from 'expo-router';
import React from 'react';
import { Platform, StyleSheet, View } from 'react-native';

import { colors, radii } from '../../src/theme';

function TabIcon({
  name,
  focused,
}: {
  name: keyof typeof Ionicons.glyphMap;
  focused: boolean;
}) {
  if (!focused) {
    return <Ionicons name={name} size={22} color={colors.muted} />;
  }
  return (
    <View style={styles.activeDot}>
      <Ionicons name={name} size={20} color={colors.ink} />
    </View>
  );
}

export default function AlumnoLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.ink,
        tabBarInactiveTintColor: colors.muted,
        tabBarLabelStyle: styles.label,
        tabBarStyle: styles.bar,
        tabBarBackground: () => <View style={styles.barBg} />,
      }}
    >
      <Tabs.Screen
        name="inicio"
        options={{
          title: 'Inicio',
          tabBarIcon: ({ focused }) => <TabIcon name="home-outline" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="permisos"
        options={{
          title: 'Permisos',
          tabBarIcon: ({ focused }) => <TabIcon name="document-text-outline" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="notas"
        options={{
          title: 'Notas',
          tabBarIcon: ({ focused }) => <TabIcon name="school-outline" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="perfil"
        options={{
          title: 'Perfil',
          tabBarIcon: ({ focused }) => <TabIcon name="person-outline" focused={focused} />,
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  bar: {
    position: 'absolute',
    backgroundColor: 'transparent',
    borderTopWidth: 0,
    elevation: 0,
    height: Platform.select({ ios: 84, default: 72 }),
    paddingBottom: Platform.select({ ios: 24, default: 10 }),
    paddingTop: 8,
    left: 48,
    right: 48,
    bottom: 16,
    borderRadius: radii.pill,
    shadowColor: '#000',
    shadowOpacity: 0.18,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 6 },
  },
  barBg: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
    backgroundColor: colors.dark,
    borderRadius: radii.pill,
  },
  label: {
    fontSize: 10,
    fontWeight: '600',
    marginTop: -2,
  },
  activeDot: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.peach,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
