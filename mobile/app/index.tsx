/**
 * Entry: redirects to the right flow based on the session.
 */
import { Redirect } from 'expo-router';
import React from 'react';
import { ActivityIndicator, View } from 'react-native';

import { isTutor, useAuth } from '../src/auth';
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
        <ActivityIndicator color={colors.purpleDeep} />
      </View>
    );
  }

  if (!session) return <Redirect href="/login" />;
  if (isTutor(session.roles)) return <Redirect href="/(tutor)" />;
  return <Redirect href="/(alumno)" />;
}
