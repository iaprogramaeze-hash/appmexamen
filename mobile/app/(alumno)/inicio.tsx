/**
 * Student home hub (S14): glossy sector bubbles in a zigzag, the coatí
 * mascot standing bottom-right, title on top — reference
 * `imagenes/diseño app/3.jpg`. Each bubble pushes its section; the
 * enrollment list itself lives in `inscripcion.tsx`.
 *
 * L39: the user dropped the "Ver mis asistencias" and "Ver mi libreta"
 * bubbles, so the hub keeps the first two sectors only.
 */
import { useRouter } from 'expo-router';
import React from 'react';
import { Image, ScrollView, StyleSheet, Text, View } from 'react-native';

import { SectorBubble } from '../../src/components/SectorBubble';
import { Screen } from '../../src/components/ui';
import { fonts, space } from '../../src/theme';

type Sector = {
  key: string;
  label: string;
  route: '/(alumno)/inscripcion' | '/(alumno)/permisos';
  sphereColors: [string, string];
};

/** The sectors kept after L39 (libreta and asistencias were dropped). */
const SECTORES: Sector[] = [
  {
    key: 'mesa',
    label: 'Inscripción a mesa',
    route: '/(alumno)/inscripcion',
    sphereColors: ['#D14E8A', '#9B7BD4'],
  },
  {
    key: 'registro',
    label: 'Registro de inscripción',
    route: '/(alumno)/permisos',
    sphereColors: ['#9B7BD4', '#4A5BC7'],
  },
];

export default function Inicio() {
  const router = useRouter();

  return (
    <Screen edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.title}>Tus sectores</Text>

        <View style={styles.bubbles}>
          {SECTORES.map((sector, i) => (
            <View
              key={sector.key}
              style={[
                styles.row,
                i % 2 === 1 ? styles.rowRight : styles.rowLeft,
                i > 0 && styles.rowOverlap,
              ]}
            >
              <SectorBubble
                label={sector.label}
                sphereColors={sector.sphereColors}
                floatDelay={i * 600}
                onPress={() => router.push(sector.route)}
              />
            </View>
          ))}
        </View>

        <Image
          source={require('../../assets/mascots/coati-parado.png')}
          style={styles.coati}
          resizeMode="contain"
          accessibilityLabel="Coatí mascota"
        />

        <View style={{ height: space(24) }} />
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  scroll: {
    paddingTop: space(6),
    paddingHorizontal: space(5),
    paddingBottom: space(6),
    gap: space(5),
  },
  title: {
    ...fonts.h1,
    textAlign: 'center',
  },
  bubbles: {
    gap: space(3),
  },
  row: {
    flexDirection: 'row',
  },
  rowLeft: {
    justifyContent: 'flex-start',
  },
  rowRight: {
    justifyContent: 'flex-end',
  },
  rowOverlap: {
    marginTop: -space(5),
  },
  coati: {
    width: 160,
    height: 220,
    alignSelf: 'flex-end',
    marginTop: -space(3),
    marginRight: space(2),
  },
});
