/**
 * Change password (S8): current password → new password → confirm.
 * Uses the dark pill inputs and slide-to-confirm CTA.
 */
import { useRouter } from 'expo-router';
import React, { useState } from 'react';
import {
  Image,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { Card, Field, PillButton, Screen } from '../src/components/ui';
import { SlideToConfirm } from '../src/components/SlideToConfirm';
import { colors, fonts, radii, space } from '../src/theme';

export default function CambiarPassword() {
  const router = useRouter();
  const [actual, setActual] = useState('');
  const [nueva, setNueva] = useState('');
  const [repetir, setRepetir] = useState('');
  const [ok, setOk] = useState(false);

  const error = (() => {
    if (!actual) return 'Ingresá tu contraseña actual.';
    if (nueva.length < 12) return 'La nueva contraseña necesita mínimo 12 caracteres.';
    if (nueva !== repetir) return 'Las contraseñas no coinciden.';
    return '';
  })();

  return (
    <Screen edges={['top', 'bottom']}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.headerRow}>
            <PillButton
              label=""
              variant="subtle"
              onPress={() => router.back()}
              style={styles.backBtn}
            />
            <Image
              source={require('../assets/mascots/tatu-estudia.png')}
              style={styles.mascot}
              resizeMode="contain"
            />
            <View style={{ flex: 1 }}>
              <Text style={fonts.h1}>Cambiar contraseña</Text>
              <Text style={fonts.muted}>Tu clave actual + una nueva de 12+ caracteres</Text>
            </View>
          </View>

          {ok ? (
            <Card style={{ alignItems: 'center', gap: space(2) }}>
              <Text style={{ fontSize: 40 }}>✅</Text>
              <Text style={fonts.h3}>Contraseña actualizada</Text>
              <Text style={[fonts.muted, { textAlign: 'center' }]}>
                Ya podés usar tu nueva contraseña para iniciar sesión.
              </Text>
              <PillButton
                label="Volver al perfil"
                variant="ghost"
                onPress={() => router.back()}
              />
            </Card>
          ) : (
            <Card>
              <Field
                label="Contraseña actual"
                icon="lock-closed-outline"
                placeholder="Tu contraseña actual"
                secureTextEntry
                value={actual}
                onChangeText={setActual}
              />
              <Field
                label="Nueva contraseña"
                icon="key-outline"
                placeholder="mínimo 12 caracteres"
                secureTextEntry
                value={nueva}
                onChangeText={setNueva}
              />
              <Field
                label="Repetir nueva contraseña"
                icon="key-outline"
                placeholder="repetí la contraseña"
                secureTextEntry
                value={repetir}
                onChangeText={setRepetir}
              />
              {error ? <Text style={styles.error}>{error}</Text> : null}
              <SlideToConfirm
                label="Deslizá para guardar"
                onConfirm={() => setOk(true)}
                disabled={!!error}
              />
              <PillButton
                label="Cancelar"
                variant="subtle"
                onPress={() => router.back()}
              />
            </Card>
          )}

          <View style={{ height: space(10) }} />
        </ScrollView>
      </KeyboardAvoidingView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  scroll: {
    padding: space(5),
    gap: space(4),
    paddingBottom: space(6),
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space(3),
  },
  backBtn: {
    minHeight: 40,
    minWidth: 40,
    paddingHorizontal: space(3),
  },
  mascot: {
    width: 64,
    height: 64,
    borderRadius: radii.pill,
  },
  error: {
    color: colors.danger,
    fontSize: 12,
    textAlign: 'center',
    minHeight: 16,
  },
});
