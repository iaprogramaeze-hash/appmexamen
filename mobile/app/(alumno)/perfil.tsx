/**
 * Student profile (S8): read-only data, change password and sign out
 * (L41: the tutor-link code was removed with the tutor role).
 */
import { useRouter } from 'expo-router';
import React, { useEffect, useState } from 'react';
import {
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { useAuth } from '../../src/auth';
import { Card, Chip, PillButton, Screen } from '../../src/components/ui';
import { guardarTecnicatura, leerTecnicatura } from '../../src/tecnicatura';
import { TECNICATURAS } from '../../src/tecnicaturaRules';
import { colors, fonts, radii, space } from '../../src/theme';

export default function PerfilAlumno() {
  const router = useRouter();
  const { session, signOut } = useAuth();
  const [tecnicatura, setTecnicatura] = useState<string | null>(null);

  // Load the one tecnicatura stored on this device (RB-02).
  useEffect(() => {
    let activo = true;
    leerTecnicatura().then((t) => {
      if (activo) setTecnicatura(t);
    });
    return () => {
      activo = false;
    };
  }, []);

  const elegirTecnicatura = async (t: string) => {
    const ok = await guardarTecnicatura(t);
    if (ok) setTecnicatura(t);
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
            <Text style={fonts.muted}>Tus datos</Text>
          </View>
        </View>

        <Card>
          <Text style={fonts.h3}>Datos de la cuenta</Text>
          <Row label="Nombre" value={session?.usuario ?? '—'} />
          <Row label="Tipo" value="Alumno" />
          <Row label="Roles" value={session?.roles.join(', ') ?? 'alumno'} />
          <Row label="Tecnicatura" value={tecnicatura ?? 'Sin elegir'} />
          {session?.demo ? (
            <Text style={styles.demoNote}>
              Sesión de demostración (el backend no está conectado).
            </Text>
          ) : null}
        </Card>

        <Card style={{ gap: space(3) }}>
          <Text style={fonts.h3}>Tecnicatura</Text>
          <Text style={[fonts.muted, { lineHeight: 20 }]}>
            Una sola por alumno. Solo ves mesas de esta tecnicatura (RB-02).
          </Text>
          <View style={styles.roleRow}>
            {TECNICATURAS.map((t) => (
              <Chip
                key={t}
                label={t}
                active={tecnicatura === t}
                onPress={() => elegirTecnicatura(t)}
              />
            ))}
          </View>
        </Card>

        <Card style={{ gap: space(3) }}>
          <Text style={fonts.h3}>Cuenta</Text>
          <PillButton
            label="Cambiar contraseña"
            variant="ghost"
            onPress={() => router.push('/cambiar-password')}
          />
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
  roleRow: {
    flexDirection: 'row',
    gap: space(2),
    flexWrap: 'wrap',
  },
});
