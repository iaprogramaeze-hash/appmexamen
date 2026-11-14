/**
 * Tutor grades view (S3/S5): read-only grades of a linked student.
 * Shows the linked-student selector; data arrives when the backend
 * endpoints (informe §3.4) exist.
 */
import React, { useMemo, useState } from 'react';
import { Image, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Card, Chip, Screen } from '../../src/components/ui';
import { colors, fonts, space } from '../../src/theme';

const ALUMNOS = [
  { id: 'a1', nombre: 'Sofía García' },
  { id: 'a2', nombre: 'Mateo Rodríguez' },
];

export default function NotasTutor() {
  const [sel, setSel] = useState(ALUMNOS[0].id);
  const alumno = useMemo(() => ALUMNOS.find((a) => a.id === sel), [sel]);

  return (
    <Screen edges={['top']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View>
          <Text style={fonts.h1}>Notas</Text>
          <Text style={fonts.muted}>
            Solo lectura de tus alumnos vinculados
          </Text>
        </View>

        {/* Linked students selector */}
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
            source={require('../../assets/mascots/calificaciones.png')}
            style={{ width: 130, height: 130 }}
            resizeMode="contain"
          />
          <Text style={styles.title}>
            Notas de {alumno?.nombre}
          </Text>
          <Text style={[fonts.muted, { textAlign: 'center' }]}>
            Las notas trimestrales aparecen acá cuando el sistema del colegio
            las exponga. Vos no podés modificarlas.
          </Text>
        </Card>

        <Card>
          <Text style={fonts.h3}>Qué podés hacer como tutor</Text>
          <Text style={[fonts.muted, { lineHeight: 20 }]}>
            Ver notas y asistencias de tus alumnos vinculados. No podés
            inscribirte a mesas ni modificar datos: tu rol es de solo lectura.
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
});
