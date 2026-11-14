/**
 * Student home: available subjects + my enrollments (prototype §home, S8),
 * styled with the gamified look: greeting, purple level card, cards with mascot.
 */
import { useRouter } from 'expo-router';
import React, { useMemo, useState } from 'react';
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

type Materia = {
  sid: string;
  nombre: string;
  anio: number;
  fecha?: string;
  inscripta?: boolean;
  condicion?: string;
  mesa?: string;
};

/** Static snapshot of the prototype demo data (backend wiring is a later task). */
const MATERIAS: Materia[] = [
  { sid: 's-rrhh', nombre: 'Administración y Gestión de RRHH', anio: 3, fecha: '10/11/2026', inscripta: true, condicion: 'REGULAR', mesa: '10/11/2026 · 14:00 · Aula 3' },
  { sid: 's-comu', nombre: 'Comunicación y Comportamiento Org.', anio: 3, fecha: '11/11/2026', inscripta: true, condicion: 'PREVIA', mesa: '11/11/2026 · 08:00 · Aula 2' },
  { sid: 's-tic3', nombre: 'Tecnología de la Información y Com. 3', anio: 3, fecha: '13/11/2026', inscripta: true, condicion: 'REGULAR', mesa: '13/11/2026 · 14:00 · Laboratorio' },
  { sid: 's-sic1', nombre: 'Sistema de Información Contable 1', anio: 3, fecha: '05/11/2026', inscripta: true, condicion: 'REGULAR', mesa: '05/11/2026 · 08:00 · Aula 1' },
  { sid: 's-prog', nombre: 'Programación de las Compras y Ventas', anio: 2, fecha: '03/11/2026' },
  { sid: 's-fica', nombre: 'Física Aplicada', anio: 2, fecha: '07/11/2026' },
  { sid: 's-ing1', nombre: 'Inglés Técnico 1', anio: 1, fecha: '04/11/2026' },
  { sid: 's-dibu', nombre: 'Dibujo Técnico', anio: 1, fecha: '06/11/2026' },
  { sid: 's-est4', nombre: 'Estadística Aplicada', anio: 4, fecha: '12/11/2026' },
  { sid: 's-adr4', nombre: 'Administración de Recursos', anio: 4, fecha: '14/11/2026' },
  { sid: 's-aud5', nombre: 'Auditoría', anio: 5, fecha: '17/11/2026' },
  { sid: 's-emp5', nombre: 'Emprendimiento', anio: 5, fecha: '18/11/2026' },
  { sid: 's-tes6', nombre: 'Trabajo Profesional', anio: 6, fecha: '20/11/2026' },
];

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
  const [inscripciones, setInscripciones] = useState<Set<string>>(
    () => new Set(MATERIAS.filter((m) => m.inscripta).map((m) => m.sid)),
  );

  const visibles = useMemo(
    () => MATERIAS.filter((m) => (anio === 0 ? true : m.anio === anio)),
    [anio],
  );
  const inscriptas = useMemo(
    () => MATERIAS.filter((m) => inscripciones.has(m.sid)),
    [inscripciones],
  );

  const toggle = (sid: string) => {
    setInscripciones((prev) => {
      const next = new Set(prev);
      if (next.has(sid)) next.delete(sid);
      else next.add(sid);
      return next;
    });
  };

  const progreso = Math.min(1, inscriptas.length / 8);

  return (
    <Screen edges={['top']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Greeting */}
        <View style={styles.greetRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.hello}>Hola, {session?.usuario ?? 'alumno'} 👋</Text>
            <Text style={fonts.muted}>Inscripción a mesas de examen</Text>
          </View>
          <ArrowCircle onPress={() => router.push('/(alumno)/perfil')} />
        </View>

        {/* Purple progress card (level card analog) */}
        <LinearGradient
          colors={[...gradientPurple.colors] as [string, string]}
          locations={[...gradientPurple.locations]}
          style={styles.levelCard}
        >
          <View style={styles.levelTop}>
            <View style={{ flex: 1 }}>
              <Text style={styles.levelTitle}>Inscripción {Math.round(progreso * 100)}%</Text>
              <Text style={styles.levelSub}>
                {inscriptas.length} de 8 asignaturas · tu próximo paso
              </Text>
            </View>
            <Text style={{ fontSize: 28 }}>🎓</Text>
          </View>
          <ProgressBar value={progreso} />
        </LinearGradient>

        {/* Mascot header for the section */}
        <Card style={{ alignItems: 'center', paddingVertical: space(4) }}>
          <Image
            source={require('../../assets/mascots/mesas-examen.png')}
            style={{ width: 120, height: 120 }}
            resizeMode="contain"
          />
          <Text style={styles.cardTitle}>Materias disponibles</Text>
          <Text style={[fonts.muted, { textAlign: 'center' }]}>
            Elegí la materia a la que querés asistir y confirmá la inscripción.
            Cada materia tiene una sola mesa.
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

        {/* Subjects */}
        <Card style={{ gap: space(3) }}>
          {visibles.map((m) => {
            const inscripta = inscripciones.has(m.sid);
            return (
              <View key={m.sid} style={styles.materiaRow}>
                <View style={{ flex: 1, gap: 2 }}>
                  <Text style={styles.materiaNombre}>{m.nombre}</Text>
                  <Text style={fonts.muted}>
                    {m.fecha ? `Mesa: ${m.fecha}` : 'Sin fecha cargada ⚠'}
                    {inscripta && m.condicion ? ` · ${m.condicion}` : ''}
                  </Text>
                </View>
                {inscripta ? (
                  <View style={styles.chipOk}>
                    <Text style={styles.chipOkText}>Inscripta</Text>
                  </View>
                ) : (
                  <PillButton
                    label="Inscribirme"
                    variant="primary"
                    onPress={() => toggle(m.sid)}
                    style={{ minHeight: 40, paddingHorizontal: space(4) }}
                  />
                )}
              </View>
            );
          })}
        </Card>

        {/* My enrollments */}
        <Card style={{ gap: space(3) }}>
          <Text style={styles.cardTitle}>Mis inscripciones</Text>
          {inscriptas.length === 0 ? (
            <Text style={fonts.muted}>Todavía no te inscribiste a ninguna mesa.</Text>
          ) : (
            inscriptas.map((m) => (
              <View key={m.sid} style={styles.materiaRow}>
                <View style={{ flex: 1, gap: 2 }}>
                  <Text style={styles.materiaNombre}>{m.nombre}</Text>
                  <Text style={fonts.muted}>
                    {m.mesa ?? m.fecha ?? '—'}
                    {m.condicion ? ` · ${m.condicion}` : ''}
                  </Text>
                </View>
                <View style={styles.chipOk}>
                  <Text style={styles.chipOkText}>Inscripta</Text>
                </View>
              </View>
            ))
          )}
          <Text style={[fonts.muted, { fontSize: 12 }]}>
            La condición (REGULAR · PREVIA · COMPLETAR ESTUDIO · EQUIVALENCIA)
            la elegís al inscribirte; por defecto es REGULAR. LIBRO/FOLIO los
            carga la escuela.
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
  materiaNombre: {
    fontWeight: '700',
    fontSize: 14,
    color: colors.ink,
  },
  chipOk: {
    backgroundColor: '#DCFCE7',
    borderRadius: radii.pill,
    paddingHorizontal: space(3),
    paddingVertical: space(1.5),
  },
  chipOkText: {
    color: colors.success,
    fontSize: 12,
    fontWeight: '700',
  },
});
