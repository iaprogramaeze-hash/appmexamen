/**
 * Student home: available subjects + my enrollments (prototype §home, S8).
 * Esqueleto visual vacío: sin datos demo ni llamadas a API hasta que el
 * backend esté disponible. Se ajusta cuando el colega exponga los endpoints.
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
import {
  ArrowCircle,
  Card,
  Chip,
  PillButton,
  ProgressBar,
  Screen,
} from '../../src/components/ui';
import { colors, fonts, gradientPurple, radii, space } from '../../src/theme';
import { LinearGradient } from 'expo-linear-gradient';

const ANIOS = [
  { key: 1, label: '1°' },
  { key: 2, label: '2°' },
  { key: 3, label: '3°' },
  { key: 4, label: '4°' },
  { key: 5, label: '5°' },
  { key: 6, label: '6°' },
  { key: 0, label: 'Todas' },
] as const;

export default function Inicio() {
  const router = useRouter();
  const { session } = useAuth();
  const [anio, setAnio] = useState<number>(0);

  return (
    <Screen edges={['top']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Greeting */}
        <View style={styles.greetRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.hello}>
              Hola, {session?.usuario ?? 'alumno'} 👋
            </Text>
            <Text style={fonts.muted}>Inscripción a mesas de examen</Text>
          </View>
          <ArrowCircle onPress={() => router.push('/(alumno)/perfil')} />
        </View>

        {/* Purple progress card (vacío hasta que lleguen los datos) */}
        <LinearGradient
          colors={[...gradientPurple.colors] as [string, string]}
          locations={[...gradientPurple.locations]}
          style={styles.levelCard}
        >
          <View style={styles.levelTop}>
            <View style={{ flex: 1 }}>
              <Text style={styles.levelTitle}>Inscripción 0%</Text>
              <Text style={styles.levelSub}>
                0 de 0 asignaturas · espera los datos del sistema
              </Text>
            </View>
            <Text style={{ fontSize: 28 }}>🎓</Text>
          </View>
          <ProgressBar value={0} />
        </LinearGradient>

        {/* Mascot header for the section */}
        <Card style={{ alignItems: 'center', paddingVertical: space(4) }}>
          <Image
            source={require('../../assets/mascots/mesas-examen.png')}
            style={{ width: 120, height: 120, borderRadius: radii.pill }}
            resizeMode="contain"
          />
          <Text style={styles.cardTitle}>Materias disponibles</Text>
          <Text style={[fonts.muted, { textAlign: 'center' }]}>
            Aquí aparecerán las mesas cuando el backend las exponga.
          </Text>
        </Card>

        {/* Year filter chips */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.chipRow}
        >
          {ANIOS.map((a) => (
            <Chip
              key={a.key}
              label={a.label}
              active={anio === a.key}
              onPress={() => setAnio(a.key)}
            />
          ))}
        </ScrollView>

        {/* Subjects (vacío) */}
        <Card style={{ gap: space(3) }}>
          <Text style={fonts.muted}>
            Sin materias cargadas todavía.
          </Text>
          <PillButton
            label="Ver ejemplo de mesa"
            variant="ghost"
            onPress={() =>
              router.push({
                pathname: '/(alumno)/mesa',
                params: {
                  materia: 'Matemática',
                  anio: '3°',
                  dia: 'Lunes 15/12',
                  hora: '08:00',
                  aula: 'Aula 12',
                },
              })
            }
          />
        </Card>

        {/* My enrollments (vacío) */}
        <Card style={{ gap: space(3) }}>
          <Text style={styles.cardTitle}>Mis inscripciones</Text>
          <Text style={fonts.muted}>
            Todavía no te inscribiste a ninguna mesa.
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
    paddingBottom: space(6),
  },
  greetRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space(3),
  },
  hello: {
    ...fonts.h2,
  },
  levelCard: {
    borderRadius: radii.lg,
    padding: space(5),
    gap: space(3),
  },
  levelTop: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space(3),
  },
  levelTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '800',
  },
  levelSub: {
    color: 'rgba(255,255,255,0.85)',
    fontSize: 13,
    marginTop: 2,
  },
  cardTitle: {
    ...fonts.h3,
  },
  chipRow: {
    gap: space(2),
    paddingVertical: space(1),
  },
  materiaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space(3),
    paddingVertical: space(1),
  },
  chipOk: {
    backgroundColor: 'rgba(74, 222, 128, 0.15)',
    borderRadius: radii.pill,
    paddingHorizontal: space(3),
    paddingVertical: space(1.5),
  },
  chipOkText: {
    color: '#4ADE80',
    fontSize: 12,
    fontWeight: '700',
  },
});
