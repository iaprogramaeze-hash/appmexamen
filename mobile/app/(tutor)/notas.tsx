/**
 * Tutor grades view — esqueleto visual vacío.
 * Se llena cuando el backend exponga las notas del alumno vinculado (S3/S5).
 */
import React from 'react';
import { Image, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Card, Chip, Screen } from '../../src/components/ui';
import { colors, fonts, radii, space } from '../../src/theme';

export default function NotasTutor() {
  return (
    <Screen edges={['top']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View>
          <Text style={fonts.h1}>Notas</Text>
          <Text style={fonts.muted}>
            Solo lectura de tus alumnos vinculados
          </Text>
        </View>

        <Card style={{ alignItems: 'center', paddingVertical: space(5) }}>
          <Image
            source={require('../../assets/mascots/calificaciones.png')}
            style={{ width: 130, height: 130, borderRadius: radii.pill }}
            resizeMode="contain"
          />
          <Text style={styles.title}>
            Aquí aparecerán las notas del alumno vinculado
          </Text>
          <Text style={[fonts.muted, { textAlign: 'center' }]}>
            Cuando el sistema del colegio las exponga las verás acá. Vos no
            podés modificarlas.
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
  title: {
    ...fonts.h3,
    color: colors.ink,
    marginTop: space(2),
  },
});
