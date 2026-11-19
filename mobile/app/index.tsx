/**
 * Entry: redirects to the right flow based on the session.
 * L40: every authenticated session lands on the student home (Inicio);
 * the tutor branch was removed from the routing.
 */
import { Redirect } from 'expo-router';
import React from 'react';
import { ActivityIndicator, View } from 'react-native';

import { useAuth } from '../src/auth';
import { colors, gradient } from '../src/theme';

export default function Index() {
  const { session, loading } = useAuth();

  if (loading) {
    return (
      <View
        style={{
          flex: 1,
          backgroundColor: gradient.colors[0],
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <ActivityIndicator color={colors.purple} />
      </View>
    );
  }

  if (!session) return <Redirect href="/login" />;
  return <Redirect href="/(alumno)" />;
}
