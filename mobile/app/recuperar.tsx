/**
 * Password recovery (S8): 2 steps — request token → set new password.
 *
 * Wired to the backend snapshot:
 *   - `POST /api/v1/auth/olvido-clave` (always 202, anti-enumeration)
 *   - `POST /api/v1/auth/restablecer-clave` (one-time token, min 12 chars)
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

import { apiErrorMessage, postOlvidoClave, postRestablecerClave } from '../src/api';
import { Card, Field, PillButton, Screen } from '../src/components/ui';
import { colors, fonts, radii, space } from '../src/theme';

export default function Recuperar() {
  const router = useRouter();
  const [paso, setPaso] = useState<1 | 2>(1);
  const [identificador, setIdentificador] = useState('');
  const [token, setToken] = useState('');
  const [clave, setClave] = useState('');
  const [repetir, setRepetir] = useState('');
  const [enviado, setEnviado] = useState(false);
  const [listo, setListo] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const pedirToken = async () => {
    if (busy) return;
    if (!identificador.trim()) {
      setError('Ingresá tu usuario o correo.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await postOlvidoClave(identificador.trim());
      setEnviado(true);
      setPaso(2);
    } catch (err) {
      setError(
        apiErrorMessage(
          err,
          'No se pudo enviar el pedido. Revisá tu conexión e intentá de nuevo.',
        ),
      );
    } finally {
      setBusy(false);
    }
  };

  const restablecer = async () => {
    if (busy) return;
    if (!token.trim()) {
      setError('Pegá el token que llegó a tu correo.');
      return;
    }
    if (clave.length < 12) {
      setError('La contraseña necesita mínimo 12 caracteres.');
      return;
    }
    if (clave !== repetir) {
      setError('Las contraseñas no coinciden.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await postRestablecerClave(token.trim(), clave);
      setListo(true);
    } catch (err) {
      setError(
        apiErrorMessage(
          err,
          'El token no es válido o ya venció. Pedí uno nuevo desde el paso 1.',
        ),
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <Screen>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.headerRow}>
            <Image
              source={require('../assets/mascots/tatu-estudia.png')}
              style={styles.mascot}
              resizeMode="contain"
            />
            <View style={{ flex: 1 }}>
              <Text style={fonts.h1}>Recuperar acceso</Text>
              <Text style={fonts.muted}>
                Paso {paso} de 2 · recuperación por correo
              </Text>
            </View>
          </View>

          {listo ? (
            <Card style={{ gap: space(2) }}>
              <Text style={styles.ok}>Contraseña restablecida ✅</Text>
              <Text style={[fonts.muted, { lineHeight: 20 }]}>
                Ya podés iniciar sesión con tu clave nueva. Por seguridad se
                cerraron las sesiones anteriores de tu cuenta.
              </Text>
              <PillButton
                label="Ir al login"
                withArrow
                onPress={() => router.replace('/login')}
              />
            </Card>
          ) : null}

          {!listo && paso === 1 && (
            <Card>
              <Text style={fonts.h3}>1 · Pedí el token</Text>
              <Text style={[fonts.muted, { lineHeight: 20 }]}>
                Ingresá tu usuario o correo: si la cuenta existe te mandamos un
                token de recuperación (vale 24 horas).
              </Text>
              <Field
                label="Usuario o correo"
                icon="person-outline"
                placeholder="alumno01 o tu correo"
                autoCapitalize="none"
                value={identificador}
                onChangeText={setIdentificador}
              />
              {error ? <Text style={styles.error}>{error}</Text> : null}
              <PillButton
                label={busy ? 'Enviando…' : 'Enviar token'}
                withArrow
                onPress={pedirToken}
              />
              <PillButton
                label="Volver al login"
                variant="subtle"
                onPress={() => router.back()}
              />
            </Card>
          )}

          {!listo && paso === 2 && (
            <Card>
              <Text style={fonts.h3}>2 · Creá tu clave nueva</Text>
              <Text style={[fonts.muted, { lineHeight: 20 }]}>
                Revisá tu correo: ahí está el{' '}
                <Text style={{ fontWeight: '700', color: colors.ink }}>
                  token de recuperación
                </Text>
                . Pegalo acá junto con tu nueva contraseña (mínimo 12
                caracteres). Si no pediste este cambio, ignorá el mensaje.
              </Text>
              {enviado && !error ? (
                <Text style={styles.ok}>
                  Pedido enviado: revisá tu correo para el token.
                </Text>
              ) : null}
              <Field
                label="Token del correo"
                icon="key-outline"
                placeholder="token que llegó a tu correo"
                autoCapitalize="none"
                autoCorrect={false}
                value={token}
                onChangeText={setToken}
              />
              <Field
                label="Nueva contraseña"
                icon="lock-closed-outline"
                placeholder="mínimo 12 caracteres"
                secureTextEntry
                value={clave}
                onChangeText={setClave}
              />
              <Field
                label="Repetir contraseña"
                icon="lock-closed-outline"
                placeholder="repetí la contraseña"
                secureTextEntry
                value={repetir}
                onChangeText={setRepetir}
              />
              {error ? <Text style={styles.error}>{error}</Text> : null}
              <PillButton
                label={busy ? 'Restableciendo…' : 'Restablecer contraseña'}
                withArrow
                onPress={restablecer}
              />
              <PillButton
                label="Volver al login"
                variant="subtle"
                onPress={() => router.replace('/login')}
              />
            </Card>
          )}

          <Card>
            <Text style={fonts.h3}>Seguridad</Text>
            <Text style={[fonts.muted, { lineHeight: 20 }]}>
              La respuesta es siempre la misma exista o no la cuenta, así no se
              adivina qué usuarios están registrados. El token se usa una sola
              vez y vence en 24 horas.
            </Text>
          </Card>
        </ScrollView>
      </KeyboardAvoidingView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  scroll: {
    padding: space(5),
    paddingBottom: space(10),
    gap: space(4),
  },
  error: {
    color: colors.danger,
    fontSize: 12,
    textAlign: 'center',
    minHeight: 16,
  },
  ok: {
    color: colors.success,
    fontSize: 13,
    fontWeight: '600',
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space(3),
    marginBottom: space(3),
  },
  mascot: {
    width: 80,
    height: 80,
    borderRadius: radii.pill,
  },
});
