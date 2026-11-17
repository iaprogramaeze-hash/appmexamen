/**
 * Reportes — listado + generación de reportes de inscripción a mesa.
 * Esqueleto visual vacío (S11): se llena cuando el backend exponga los
 * endpoints de reportes para la app (gate `reporte.exportar`).
 */
import React from 'react';
import { Image, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Card, PillButton, Screen } from '../../src/components/ui';
import { colors, fonts, radii, space } from '../../src/theme';

export default function Reportes() {
  return (
    <Screen edges={['top']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View>
          <Text style={fonts.h1}>Reportes</Text>
          <Text style={fonts.muted}>
            Reportes de tu inscripción a mesas
          </Text>
        </View>

        <Card style={{ alignItems: 'center', paddingVertical: space(5) }}>
          <Image
            source={require('../../assets/mascots/mesas-examen.png')}
            style={{ width: 140, height: 140, borderRadius: radii.pill }}
            resizeMode="contain"
          />
          <Text style={styles.title}>Tus reportes aparecen acá</Text>
          <Text style={[fonts.muted, { textAlign: 'center' }]}>
            Cuando generes un reporte de inscripción a una mesa, va a quedar
            listado acá.
          </Text>
        </Card>

        <Card style={{ gap: space(4) }}>
          <Text style={fonts.h3}>Generar reporte de inscripción</Text>
          <Text style={[fonts.muted, { lineHeight: 20 }]}>
            Elige la mesa y genera el reporte de tu inscripción con un toque.
          </Text>
          <PillButton label="Generar reporte" disabled withArrow />
          <Text style={[fonts.muted, { textAlign: 'center' }]}>
            Disponible cuando el backend exponga la acción para la app.
          </Text>
        </Card>

        <Card>
          <Text style={fonts.h3}>Cómo funciona</Text>
          <Text style={[fonts.muted, { lineHeight: 20 }]}>
            El backend arma el reporte desde tus inscripciones a mesas. Acá
            puedes pedirlo y verlo cuando esté listo.
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
