/**
 * Tutor profile: account data, link a student with a code (S4),
 * unlink, and sign out. Read-only role (S3).
 */
import { useRouter } from 'expo-router';
import React, { useState } from 'react';
import {
  Image,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { useAuth } from '../../src/auth';
import { Card, Field, PillButton, Screen } from '../../src/components/ui';
import { colors, fonts, radii, space } from '../../src/theme';

type Vinculo = { id: string; nombre: string; documento: string };

export default function PerfilTutor() {
  const router = useRouter();
  const { session, signOut } = useAuth();
  const [codigo, setCodigo] = useState('');
  const [vinculados, setVinculados] = useState<Vinculo[]>([
    { id: 'a1', nombre: 'Sofía García', documento: '41.234.567' },
  ]);
  const [mensaje, setMensaje] = useState<{ ok: boolean; text: string } | null>(null);

  const vincular = () => {
    const limpio = codigo.trim().toUpperCase();
    if (limpio.length < 6) {
      setMensaje({ ok: false, text: 'Ingresá el código completo (ej.: K7M-2QX).' });
      return;
    }
    // Backend flow (informe §3.3): pending endpoint -> optimistic demo link.
    setVinculados((prev) =>
      prev.some((v) => v.nombre === 'Alumno nuevo')
        ? prev
        : [...prev, { id: `n${prev.length}`, nombre: 'Alumno nuevo', documento: '—' }],
    );
    setCodigo('');
    setMensaje({ ok: true, text: 'Alumno vinculado. Ya podés ver sus notas y asistencias.' });
  };

  const desvincular = (id: string) => {
    setVinculados((prev) => prev.filter((v) => v.id !== id));
    setMensaje(null);
  };

  const cerrarSesion = async () => {
    await signOut();
    router.replace('/login');
  };

  return (
    <Screen edges={['top']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.headerRow}>
          <Image
            source={require('../../assets/mascots/tatu-estudia.png')}
            style={styles.mascot}
            resizeMode="contain"
          />
          <View style={{ flex: 1 }}>
            <Text style={fonts.h1}>Perfil</Text>
            <Text style={fonts.muted}>Tus alumnos vinculados</Text>
          </View>
        </View>

        <Card>
          <Text style={fonts.h3}>Datos de la cuenta</Text>
          <Row label="Nombre" value={session?.usuario ?? '—'} />
          <Row label="Tipo" value="Tutor / Padre" />
          <Row label="Roles" value={session?.roles.join(', ') ?? 'tutor'} />
        </Card>

        <Card style={{ gap: space(3) }}>
          <Text style={fonts.h3}>Vincular alumno</Text>
          <Text style={[fonts.muted, { lineHeight: 20 }]}>
            Pedile al alumno su código (lo genera en su Perfil) y pegalo acá.
            Con el vínculo podés ver sus notas y asistencias.
          </Text>
          <Field
            label="Código del alumno"
            icon="key-outline"
            placeholder="K7M-2QX"
            autoCapitalize="characters"
            autoCorrect={false}
            value={codigo}
            onChangeText={setCodigo}
          />
          <PillButton label="Vincular alumno" withArrow onPress={vincular} />
          {mensaje ? (
            <Text
              style={{
                fontSize: 13,
                color: mensaje.ok ? colors.success : colors.danger,
                textAlign: 'center',
              }}
            >
              {mensaje.text}
            </Text>
          ) : null}
        </Card>

        <Card style={{ gap: space(3) }}>
          <Text style={fonts.h3}>Alumnos vinculados</Text>
          {vinculados.length === 0 ? (
            <Text style={fonts.muted}>Todavía no vinculaste alumnos.</Text>
          ) : (
            vinculados.map((v) => (
              <View key={v.id} style={styles.vinculoRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.nombre}>{v.nombre}</Text>
                  <Text style={fonts.muted}>D.N.I. {v.documento}</Text>
                </View>
                <PillButton
                  label="Quitar"
                  variant="subtle"
                  onPress={() => desvincular(v.id)}
                  style={{ minHeight: 36, paddingHorizontal: space(3) }}
                />
              </View>
            ))
          )}
        </Card>

        <Card style={{ gap: space(3) }}>
          <Text style={fonts.h3}>Cuenta</Text>
          <PillButton label="Cambiar contraseña" variant="ghost" onPress={() => router.push('/cambiar-password')} />
          <PillButton label="Cerrar sesión" variant="ghost" onPress={cerrarSesion} />
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
  vinculoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space(3),
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
    paddingBottom: space(2.5),
  },
  nombre: {
    fontWeight: '700',
    fontSize: 14,
    color: colors.ink,
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
