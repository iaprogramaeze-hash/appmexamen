/**
 * Tutor attendance view (S3/S6): read-only attendance of a linked student.
 * Data arrives when the backend endpoint (informe §3.5) exists.
 */
import React, { useMemo, useState } from 'react';
import { Image, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Card, Chip, Screen } from '../../src/components/ui';
import { colors, fonts, radii, space } from '../../src/theme';

const ALUMNOS = [
  { id: 'a1', nombre: 'Sofía García' },
  { id: 'a2', nombre: 'Mateo Rodríguez' },
];

/** Sample structure — real rows come from the backend; kept shape-only. */
type Asistencia = { fecha: string; materia: string; presente: boolean };

const MUESTRA: Asistencia[] = [
  { fecha: '10/11/2026', materia: 'Matemática', presente: true },
  { fecha: '09/11/2026', materia: 'Programación', presente: true },
  { fecha: '07/11/2026', materia: 'Física Aplicada', presente: false },
];

export default function AsistenciasTutor() {
  const [sel, setSel] = useState(ALUMNOS[0].id);
  const alumno = useMemo(() => ALUMNOS.find((a) => a.id === sel), [sel]);

  return (
    <Screen edges={['top']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View>
          <Text style={fonts.h1}>Asistencias</Text>
          <Text style={fonts.muted}>
            Registro de asistencia a clases · solo lectura
          </Text>
        </View>

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.chipRow}
        >
          {ALUMNOS.map((a) => (
            <Chip
              key={a.id}
              label={a.nombre}
              active={a.id === sel}
              onPress={() => setSel(a.id)}
            />
          ))}
        </ScrollView>

        <Card style={{ alignItems: 'center', paddingVertical: space(5) }}>
          <Image
            source={require('../../assets/mascots/asistencia.png')}
            style={{ width: 130, height: 130 }}
            resizeMode="contain"
          />
          <Text style={styles.title}>Asistencias de {alumno?.nombre}</Text>
          <Text style={[fonts.muted, { textAlign: 'center' }]}>
            Cuando el sistema del colegio exponga el registro vas a ver fechas
            y materias acá.
          </Text>
        </Card>

        <Card style={{ gap: space(3) }}>
          <Text style={fonts.h3}>Cómo funciona</Text>
          <Text style={[fonts.muted, { lineHeight: 20 }]}>
            La asistencia la carga el sistema del colegio (no desde la app).
            Este rol solo la lee.
          </Text>
        </Card>

        <View style={{ height: space(24) }} />
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  scroll: {
    padding: space(5),
    gap: space(4),
  },
  chipRow: {
    gap: space(2),
  },
  title: {
    ...fonts.h3,
    color: colors.ink,
    marginTop: space(2),
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space(3),
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
    paddingBottom: space(2.5),
  },
  badge: {
    borderRadius: radii.sm,
    paddingHorizontal: space(2.5),
    paddingVertical: space(1),
  },
});
