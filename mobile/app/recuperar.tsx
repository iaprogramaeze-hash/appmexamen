/**
 * Password recovery (S8): 2 steps — request token → set new password.
 * Matches the prototype copy (24h token, one-time use, min 12 chars).
 */
import { useRouter } from 'expo-router';
import React, { useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { Card, Field, PillButton, Screen } from '../src/components/ui';
import { colors, fonts, space } from '../src/theme';

export default function Recuperar() {
  const router = useRouter();
  const [paso, setPaso] = useState<1 | 2>(1);
  const [identificador, setIdentificador] = useState('');
  const [token, setToken] = useState('');
  const [clave, setClave] = useState('');
  const [repetir, setRepetir] = useState('');
  const [enviado, setEnviado] = useState(false);
  const [error, setError] = useState('');

  const pedirToken = () => {
    if (!identificador.trim()) {
      setError('Ingresá tu usuario o correo.');
      return;
    }
    setError('');
    setEnviado(true);
    setPaso(2);
  };

  const restablecer = () => {
    if (clave.length < 12) {
      setError('La contraseña necesita mínimo 12 caracteres.');
      return;
    }
    if (clave !== repetir) {
      setError('Las contraseñas no coinciden.');
      return;
    }
    setError('');
    router.replace('/login');
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
          <View>
            <Text style={fonts.h1}>Recuperar acceso</Text>
            <Text style={fonts.muted}>
              Paso {paso} de 2 · recuperación por correo
            </Text>
          </View>

          {paso === 1 && (
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
              <PillButton label="Enviar token" withArrow onPress={pedirToken} />
              <PillButton
                label="Volver al login"
                variant="subtle"
                onPress={() => router.back()}
              />
            </Card>
          )}

          {paso === 2 && (
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
                <Text style={styles.ok}>Token enviado (simulado por ahora).</Text>
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
                label="Restablecer contraseña"
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
});
