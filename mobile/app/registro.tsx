/**
 * Account creation (S8): 3 steps like the prototype — form → verify email →
 * pending approval. Role picker: alumno (default) or tutor (S3).
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

import { Card, Chip, Field, PillButton, Screen } from '../src/components/ui';
import { SlideToConfirm } from '../src/components/SlideToConfirm';
import { colors, fonts, radii, space } from '../src/theme';

type Paso = 1 | 2 | 3;

export default function Registro() {
  const router = useRouter();
  const [paso, setPaso] = useState<Paso>(1);
  const [rol, setRol] = useState<'alumno' | 'tutor'>('alumno');
  const [form, setForm] = useState({
    nombre: '',
    apellido: '',
    dni: '',
    email: '',
    telefono: '',
    password: '',
    repetir: '',
    codigo: '',
  });

  const set = (k: keyof typeof form) => (v: string) =>
    setForm((f) => ({ ...f, [k]: v }));

  const errorForm = (() => {
    if (paso !== 1) return '';
    if (!form.nombre.trim() || !form.apellido.trim()) return 'Ingresá nombre y apellido.';
    if (!form.dni.trim()) return 'El D.N.I. es obligatorio (uno por cuenta).';
    if (!form.email.includes('@')) return 'Ingresá un correo válido.';
    if (form.password.length < 12) return 'La contraseña necesita mínimo 12 caracteres.';
    if (form.password !== form.repetir) return 'Las contraseñas no coinciden.';
    return '';
  })();

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
              <Text style={fonts.h1}>Crear cuenta</Text>
              <Text style={fonts.muted}>
                Paso {paso} de 3 · registro libre · un D.N.I. = una cuenta
              </Text>
            </View>
          </View>

          {paso === 1 && (
            <Card>
              {/* Role picker (S3) */}
              <View style={{ gap: space(2) }}>
                <Text style={styles.label}>Tipo de cuenta</Text>
                <View style={styles.roleRow}>
                  <Chip
                    label="Soy alumno"
                    active={rol === 'alumno'}
                    onPress={() => setRol('alumno')}
                  />
                  <Chip
                    label="Soy tutor / padre"
                    active={rol === 'tutor'}
                    onPress={() => setRol('tutor')}
                  />
                </View>
              </View>

              <Field
                label="Nombre"
                icon="person-outline"
                placeholder="María Soledad"
                value={form.nombre}
                onChangeText={set('nombre')}
              />
              <Field
                label="Apellido"
                icon="person-outline"
                placeholder="Pérez"
                value={form.apellido}
                onChangeText={set('apellido')}
              />
              <Field
                label="D.N.I. (único)"
                icon="card-outline"
                placeholder="38.456.789"
                keyboardType="number-pad"
                value={form.dni}
                onChangeText={set('dni')}
              />
              <Field
                label="Correo electrónico"
                icon="mail-outline"
                placeholder="maria.perez@correo.com"
                autoCapitalize="none"
                keyboardType="email-address"
                value={form.email}
                onChangeText={set('email')}
              />
              <Field
                label="Teléfono"
                icon="call-outline"
                placeholder="376 412-3456"
                keyboardType="phone-pad"
                value={form.telefono}
                onChangeText={set('telefono')}
              />
              <Field
                label="Contraseña"
                icon="lock-closed-outline"
                placeholder="mínimo 12 caracteres"
                secureTextEntry
                value={form.password}
                onChangeText={set('password')}
              />
              <Field
                label="Repetir contraseña"
                icon="lock-closed-outline"
                placeholder="repetí la contraseña"
                secureTextEntry
                value={form.repetir}
                onChangeText={set('repetir')}
              />

              {errorForm ? <Text style={styles.error}>{errorForm}</Text> : null}

              <SlideToConfirm
                label="Deslizá para crear cuenta"
                onConfirm={() => setPaso(2)}
                disabled={!!errorForm}
              />
              <Text style={[fonts.muted, { textAlign: 'center' }]}>
                Al crear la cuenta te llega un código al correo para
                verificarlo.
              </Text>
              <PillButton
                label="Volver al login"
                variant="subtle"
                onPress={() => router.back()}
              />
            </Card>
          )}

          {paso === 2 && (
            <Card>
              <Text style={fonts.h3}>Verificá tu correo</Text>
              <Text style={[fonts.muted, { lineHeight: 20 }]}>
                Mandamos un código de 6 dígitos a{' '}
                <Text style={{ fontWeight: '700', color: colors.ink }}>
                  {form.email || 'tu correo'}
                </Text>
                .
              </Text>
              <Field
                label="Código de verificación"
                icon="shield-checkmark-outline"
                placeholder="– – – – – –"
                keyboardType="number-pad"
                maxLength={6}
                value={form.codigo}
                onChangeText={set('codigo')}
              />
              <SlideToConfirm
                label="Deslizá para validar"
                onConfirm={() => setPaso(3)}
                disabled={form.codigo.length !== 6}
              />
              <PillButton label="Reenviar código (60 s)" variant="subtle" />
              <PillButton
                label="Volver"
                variant="subtle"
                onPress={() => setPaso(1)}
              />
            </Card>
          )}

          {paso === 3 && (
            <Card>
              <Text style={fonts.h3}>Cuenta creada ✅</Text>
              <Text style={[fonts.muted, { lineHeight: 20 }]}>
                Tu cuenta quedó registrada y el correo verificado. Pero{' '}
                <Text style={{ fontWeight: '700', color: colors.ink }}>
                  está pendiente de aprobación
                </Text>{' '}
                en el sistema del colegio (el otro sistema).
              </Text>
              <View style={styles.aviso}>
                <Text style={styles.avisoText}>
                  Tu cuenta no se activa hasta que el otro sistema la apruebe.
                </Text>
              </View>
              <Text style={[fonts.muted, { lineHeight: 20 }]}>
                Vas a recibir un correo cuando tu cuenta sea aprobada. Mientras
                tanto no podés iniciar sesión.
              </Text>
              <PillButton
                label="Volver al login"
                withArrow
                onPress={() => router.replace('/login')}
              />
            </Card>
          )}
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
  label: {
    fontWeight: '600',
    fontSize: 13,
    color: colors.ink,
  },
  roleRow: {
    flexDirection: 'row',
    gap: space(2),
    flexWrap: 'wrap',
  },
  error: {
    color: colors.danger,
    fontSize: 12,
    textAlign: 'center',
    minHeight: 16,
  },
  aviso: {
    backgroundColor: 'rgba(209, 78, 138, 0.15)',
    borderRadius: 16,
    padding: space(4),
    borderWidth: 1,
    borderColor: 'rgba(209, 78, 138, 0.4)',
  },
  avisoText: {
    color: '#F0A3C0',
    fontSize: 13,
    fontWeight: '600',
    lineHeight: 19,
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
