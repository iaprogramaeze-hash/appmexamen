/**
 * Login — dark space-app style: dark purple gradient, big mascot,
 * dark rounded card, magenta→purple gradient CTA.
 * Functional copy matches the approved prototype (S8).
 */
import { useRouter } from 'expo-router';
import React, { useState } from 'react';
import {
  Image,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { useAuth } from '../src/auth';
import { Card, Field, PillButton, Screen } from '../src/components/ui';
import { SlideToConfirm } from '../src/components/SlideToConfirm';
import { colors, fonts, radii, space } from '../src/theme';

export default function Login() {
  const router = useRouter();
  const { signIn } = useAuth();
  const [usuario, setUsuario] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const onSubmit = async () => {
    if (busy) return;
    setBusy(true);
    setError('');
    const res = await signIn(usuario, password);
    setBusy(false);
    if (!res.ok) {
      setError(res.error ?? 'No se pudo iniciar sesión.');
      return;
    }
    router.replace('/');
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
          {/* Mascot hero */}
          <View style={styles.hero}>
            <Image
              source={require('../assets/mascots/tatu-estudia.png')}
              style={styles.mascot}
              resizeMode="contain"
            />
            <View style={styles.schoolBadge}>
              <Text style={styles.schoolName}>E.P.E.T. N°36</Text>
            </View>
          </View>

          <Text style={styles.title}>
            Iniciar sesión
          </Text>
          <Text style={[fonts.muted, { marginBottom: space(5) }]}>
            Acceso de alumnos y tutores · el otro sistema aprueba cada cuenta
          </Text>

          <Card>
            <Field
              label="Usuario o correo"
              icon="person-outline"
              placeholder="D.N.I. o correo"
              autoCapitalize="none"
              autoComplete="username"
              value={usuario}
              onChangeText={setUsuario}
            />
            <Field
              label="Contraseña"
              icon="lock-closed-outline"
              placeholder="Tu contraseña"
              secureTextEntry={!showPw}
              value={password}
              onChangeText={setPassword}
            />
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={showPw ? 'Ocultar contraseña' : 'Mostrar contraseña'}
              onPress={() => setShowPw((v) => !v)}
              style={styles.eye}
            >
              <Text style={{ fontSize: 13, color: colors.purple, fontWeight: '600' }}>
                {showPw ? 'Ocultar' : 'Mostrar'}
              </Text>
            </Pressable>

            <SlideToConfirm
              label={busy ? 'Ingresando…' : 'Deslizá para iniciar sesión'}
              onConfirm={onSubmit}
              disabled={busy}
            />
            {error ? <Text style={styles.error}>{error}</Text> : null}

            <PillButton
              label="Crear cuenta"
              variant="ghost"
              onPress={() => router.push('/registro')}
            />

            <View style={styles.divider} />

            <Text style={[fonts.muted, { textAlign: 'center' }]}>
              ¿Olvidaste tu contraseña? Recuperá el acceso con tu correo: te
              mandamos un token para crear una clave nueva.
            </Text>
            <PillButton
              label="Recuperar acceso"
              variant="subtle"
              onPress={() => router.push('/recuperar')}
            />
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
    gap: space(2),
  },
  hero: {
    alignItems: 'center',
    marginBottom: space(4),
  },
  mascot: {
    width: 200,
    height: 200,
    borderRadius: radii.pill,
  },
  schoolBadge: {
    marginTop: space(3),
    backgroundColor: colors.surface,
    borderRadius: radii.pill,
    paddingHorizontal: space(4),
    paddingVertical: space(1.5),
    borderWidth: 1,
    borderColor: colors.purple,
  },
  schoolName: {
    fontWeight: '700',
    color: colors.ink,
    fontSize: 13,
    letterSpacing: 0.4,
  },
  title: {
    ...fonts.h1,
    textAlign: 'left',
  },
  eye: {
    alignSelf: 'flex-end',
    marginTop: -space(2),
    padding: space(1),
  },
  error: {
    color: colors.danger,
    fontSize: 12,
    textAlign: 'center',
    minHeight: 16,
  },
  divider: {
    height: 1,
    backgroundColor: colors.line,
    opacity: 0.4,
    marginVertical: space(1),
  },
});
