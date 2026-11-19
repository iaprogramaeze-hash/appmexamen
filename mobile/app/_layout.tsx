/**
 * Root layout: providers + navigation stack for the whole app.
 */
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import React from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { AuthProvider } from '../src/auth';
import { gradient } from '../src/theme';

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <StatusBar style="light" />
        <Stack
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: gradient.colors[0] },
          }}
        >
          <Stack.Screen name="index" />
          <Stack.Screen name="login" />
          <Stack.Screen name="registro" />
          <Stack.Screen name="recuperar" />
          <Stack.Screen name="(alumno)" />
        </Stack>
      </AuthProvider>
    </SafeAreaProvider>
  );
}
