/**
 * Change password (S8): current password → new password → confirm.
 *
 * Wired to `POST /api/v1/auth/cambiar-clave` (`{ clave_actual, clave_nueva }`).
 * The response carries a fresh access token because the backend bumps
 * `token_version`; the session stores it so the user stays logged in.
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

import { useAuth } from '../src/auth';
import { ApiError, apiErrorMessage, postCambiarClave } from '../src/api';
import { Card, Field, PillButton, Screen } from '../src/components/ui';
import { SlideToConfirm } from '../src/components/SlideToConfirm';
import { colors, fonts, radii, space } from '../src/theme';

export default function CambiarPassword() {
  const router = useRouter();
  const { session, updateAccess } = useAuth();
  const [actual, setActual] = useState('');
  const [nueva, setNueva] = useState('');
  const [repetir, setRepetir] = useState('');
  const [ok, setOk] = useState(false);
  const [busy, setBusy] = useState(false);
  const [serverError, setServerError] = useState('');

  const error = (() => {
    if (!actual) return 'Ingresá tu contraseña actual.';
    if (nueva.length < 12) return 'La nueva contraseña necesita mínimo 12 caracteres.';
    if (nueva !== repetir) return 'Las contraseñas no coinciden.';
    return '';
  })();

  const guardar = async () => {
    if (busy) return;
    if (error) {
      setServerError(error);
      return;
    }
    setServerError('');

    if (!session || session.demo) {
      setServerError(
        'Necesitás una sesión real para cambiar la clave. Conectá el backend y volvé a entrar.',
      );
      return;
    }

    setBusy(true);
    try {
      const { access } = await postCambiarClave(session.access, actual, nueva);
      await updateAccess(access);
      setOk(true);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.code === 'clave-invalida') {
          setServerError('La contraseña actual no es correcta.');
        } else if (err.code === 'cuenta-suspendida') {
          setServerError('La cuenta está suspendida. Contactá a la escuela.');
        } else if (err.status === 401) {
          setServerError('Tu sesión venció. Volvé a iniciar sesión.');
        } else {
          setServerError(apiErrorMessage(err, 'No se pudo cambiar la contraseña.'));
        }
      } else {
        setServerError('No se pudo conectar con el servidor. Revisá tu conexión.');
      }
    } finally {
      setBusy(false);
    }
  };

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
                Ya podés usar tu nueva contraseña. Las demás sesiones de tu
                cuenta quedaron cerradas por seguridad.
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
              {serverError ? <Text style={styles.error}>{serverError}</Text> : null}
              <SlideToConfirm
                label={busy ? 'Guardando…' : 'Deslizá para guardar'}
                onConfirm={guardar}
                disabled={!!error || busy}
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
