/**
 * Tutor attendance view — esqueleto visual vacío.
 * Se llena cuando el backend exponga el registro de asistencia (S3/S6).
 */
import React from 'react';
import { Image, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Card, Chip, Screen } from '../../src/components/ui';
import { colors, fonts, radii, space } from '../../src/theme';

export default function AsistenciasTutor() {
  return (
    <Screen edges={['top']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View>
          <Text style={fonts.h1}>Asistencias</Text>
          <Text style={fonts.muted}>
            Registro de asistencia a clases · solo lectura
          </Text>
        </View>

        <Card style={{ alignItems: 'center', paddingVertical: space(5) }}>
          <Image
            source={require('../../assets/mascots/asistencia.png')}
            style={{ width: 130, height: 130, borderRadius: radii.pill }}
            resizeMode="contain"
          />
          <Text style={styles.title}>
            Aquí aparecerán las asistencias del alumno vinculado
          </Text>
          <Text style={[fonts.muted, { textAlign: 'center' }]}>
            Cuando el sistema del colegio exponga el registro las verás acá.
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
});
