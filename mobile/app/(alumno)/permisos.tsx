/**
 * Student permits (permisos de examen) — esqueleto visual vacío.
 * Se llena cuando el backend exponga los permisos generados (S8).
 */
import React from 'react';
import { Image, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Card, Chip, Screen } from '../../src/components/ui';
import { colors, fonts, radii, space } from '../../src/theme';

export default function Permisos() {
  return (
    <Screen edges={['top']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View>
          <Text style={fonts.h1}>Mis permisos</Text>
          <Text style={fonts.muted}>
            Permisos de examen generados con tu inscripción (RB-18)
          </Text>
        </View>

        <Card style={{ alignItems: 'center', paddingVertical: space(5) }}>
          <Image
            source={require('../../assets/mascots/tatu-estudia.png')}
            style={{ width: 140, height: 140, borderRadius: radii.pill }}
            resizeMode="contain"
          />
          <Text style={styles.title}>Tus permisos aparecen acá</Text>
          <Text style={[fonts.muted, { textAlign: 'center' }]}>
            Cuando te inscribas a una mesa, el permiso de examen se genera
            automáticamente (RB-18).
          </Text>
        </Card>

        <Card style={{ gap: space(4) }}>
          <Text style={fonts.muted}>
            Sin permisos cargados todavía.
          </Text>
        </Card>

        <Card>
          <Text style={fonts.h3}>Cómo funcionan</Text>
          <Text style={[fonts.muted, { lineHeight: 20 }]}>
            Cada grupo de condiciones genera su permiso (RB-18). El límite es
            por condición (RB-03): PREVIA hasta 3, REGULAR hasta 8; Completar
            Estudio y Equivalencia sin tope. LIBRO/FOLIO los carga la escuela.
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
