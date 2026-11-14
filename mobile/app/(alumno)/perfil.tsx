/**
 * Student profile (S4/S8): read-only data, change password, sign out,
 * and the tutor-link code generator (the student controls the code).
 */
import { useRouter } from 'expo-router';
import React, { useEffect, useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { useAuth } from '../../src/auth';
import { Card, PillButton, Screen } from '../../src/components/ui';
import { colors, fonts, radii, space } from '../../src/theme';

/** Generates a short human-readable link code (like K7M-2QX). */
function makeCode(): string {
  const alphabet = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
  const pick = () => alphabet[Math.floor(Math.random() * alphabet.length)];
  const chunk = () =>
    Array.from({ length: 3 }, pick).join('');
  return `${chunk()}-${Array.from({ length: 3 }, pick).join('')}`;
}

export default function PerfilAlumno() {
  const router = useRouter();
  const { session, signOut } = useAuth();
  const [codigo, setCodigo] = useState<string | null>(null);
  const [restante, setRestante] = useState(0);

  // Countdown for the link code lifetime (10 min, S4 / informe §3.3).
  useEffect(() => {
    if (!codigo || restante <= 0) return;
    const t = setTimeout(() => setRestante((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [codigo, restante]);

  const generar = () => {
    setCodigo(makeCode());
    setRestante(600);
  };

  const cerrarSesion = async () => {
    await signOut();
    router.replace('/login');
  };

  return (
    <Screen edges={['top']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View>
          <Text style={fonts.h1}>Perfil</Text>
          <Text style={fonts.muted}>Tus datos y tu código de tutor</Text>
        </View>

        <Card>
          <Text style={fonts.h3}>Datos de la cuenta</Text>
          <Row label="Nombre" value={session?.usuario ?? '—'} />
          <Row label="Tipo" value="Alumno" />
          <Row label="Roles" value={session?.roles.join(', ') ?? 'alumno'} />
          {session?.demo ? (
            <Text style={styles.demoNote}>
              Sesión de demostración (el backend no está conectado).
            </Text>
          ) : null}
        </Card>

        <Card style={{ gap: space(3) }}>
          <Text style={fonts.h3}>Código para vincular un tutor</Text>
          <Text style={[fonts.muted, { lineHeight: 20 }]}>
            Generá un código y pasáselo a tu tutor o padre: con él se vincula
            desde su cuenta y puede ver tus notas y asistencias. El código vale
            10 minutos y sirve una sola vez.
          </Text>

          {codigo ? (
            <View style={styles.codeBox}>
              <Text style={styles.codeText}>{codigo}</Text>
              <Text style={styles.codeTimer}>
                {restante > 0
                  ? `Vence en ${Math.floor(restante / 60)}:${String(restante % 60).padStart(2, '0')}`
                  : 'Vencido — generá uno nuevo'}
              </Text>
            </View>
          ) : null}

          <PillButton
            label={codigo && restante > 0 ? 'Generar otro código' : 'Generar código'}
            withArrow
            onPress={generar}
          />
        </Card>

        <Card style={{ gap: space(3) }}>
          <Text style={fonts.h3}>Cuenta</Text>
          <PillButton
            label="Cerrar sesión"
            variant="ghost"
            onPress={cerrarSesion}
          />
        </Card>

        <View style={{ height: space(24) }} />
      </ScrollView>
    </Screen>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.row}>
      <Text style={fonts.muted}>{label}</Text>
      <Text style={styles.rowValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  scroll: {
    padding: space(5),
    gap: space(4),
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: space(3),
    paddingVertical: space(1),
  },
  rowValue: {
    fontWeight: '600',
    color: colors.ink,
    fontSize: 14,
    flexShrink: 1,
    textAlign: 'right',
  },
  demoNote: {
    fontSize: 12,
    color: colors.purpleDeep,
    fontStyle: 'italic',
  },
  codeBox: {
    backgroundColor: colors.surfaceSoft,
    borderRadius: radii.lg,
    borderWidth: 1.5,
    borderColor: colors.purple,
    padding: space(5),
    alignItems: 'center',
    gap: space(1),
  },
  codeText: {
    fontSize: 34,
    fontWeight: '800',
    letterSpacing: 4,
    color: colors.ink,
  },
  codeTimer: {
    fontSize: 13,
    color: colors.purpleDeep,
    fontWeight: '600',
  },
});
