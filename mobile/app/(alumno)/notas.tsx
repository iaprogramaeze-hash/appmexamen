/**
 * Student grades (S5): trimestral grades per subject, read-only.
 * Data source is the backend (from SIGME); shows an empty/loading note
 * until the endpoint exists — no fake grades.
 */
import React from 'react';
import { Image, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Card, Screen } from '../../src/components/ui';
import { colors, fonts, radii, space } from '../../src/theme';

export default function NotasAlumno() {
  return (
    <Screen edges={['top']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View>
          <Text style={fonts.h1}>Mis notas</Text>
          <Text style={fonts.muted}>
            Notas trimestrales por materia · vienen del sistema del colegio
          </Text>
        </View>

        <Card style={{ alignItems: 'center', paddingVertical: space(5) }}>
          <Image
            source={require('../../assets/mascots/calificaciones.png')}
            style={{ width: 140, height: 140, borderRadius: radii.pill }}
            resizeMode="contain"
          />
          <Text style={styles.title}>Tus notas aparecen acá</Text>
          <Text style={[fonts.muted, { textAlign: 'center' }]}>
            Cuando el sistema del colegio exponga tus notas trimestrales vas a
            verlas materias por materias.
          </Text>
        </Card>

        <Card>
          <Text style={fonts.h3}>Cómo se cargan</Text>
          <Text style={[fonts.muted, { lineHeight: 20 }]}>
            Las notas las carga el sistema del colegio (no se cargan desde la
            app). Acá solo se leen: cada materia muestra su nota de 1°, 2° y 3°
            trimestre.
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
  title: {
    ...fonts.h3,
    color: colors.ink,
    marginTop: space(2),
  },
});
