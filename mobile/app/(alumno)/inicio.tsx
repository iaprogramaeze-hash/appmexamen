/**
 * Student home: available subjects + my enrollments (prototype §home, S8).
 *
 * Wired to the real backend snapshot:
 *   - `GET /api/v1/mesas-disponibles` (live tables of the open window)
 *   - `GET /api/v1/mis-inscripciones` (the student's own enrollments)
 *
 * A demo session (backend unreachable at login) shows a clear notice instead
 * of inventing data.
 */
import { useFocusEffect, useRouter } from 'expo-router';
import React, { useCallback, useState } from 'react';
import {
  Image,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { useAuth } from '../../src/auth';
import {
  ApiError,
  apiErrorMessage,
  fetchConvocatoriaVigente,
  fetchMesasDisponibles,
  fetchMisInscripciones,
  type ConvocatoriaVigente,
  type MesaDisponible,
  type MisInscripcion,
} from '../../src/api';
import {
  ArrowCircle,
  Card,
  Chip,
  PillButton,
  ProgressBar,
  Screen,
} from '../../src/components/ui';
import { leerTecnicatura } from '../../src/tecnicatura';
import { filtraMesasPorTecnicatura } from '../../src/tecnicaturaRules';
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

/** "1er Año" -> 1; unknown format -> 0 (never matches a year chip). */
function anioDe(curso: string): number {
  const match = /^(\d)/.exec(curso);
  return match ? Number(match[1]) : 0;
}

/** "2026-12-15" -> "15/12". */
function formatFecha(iso: string): string {
  const [, mes, dia] = iso.split('-');
  return mes && dia ? `${dia}/${mes}` : iso;
}

/** "08:00:00" -> "08:00". */
function formatHora(hora: string | null): string {
  return hora ? hora.slice(0, 5) : '—';
}

function mensajeDeError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.code === 'ventana-cerrada') {
      return 'La ventana de inscripción está cerrada.';
    }
    return apiErrorMessage(err, 'El servidor rechazó la consulta.');
  }
  return 'No se pudo conectar con el servidor. Revisá que el backend esté levantado.';
}

export default function Inicio() {
  const router = useRouter();
  const { session } = useAuth();
  const [anio, setAnio] = useState<number>(0);
  const [mesas, setMesas] = useState<MesaDisponible[]>([]);
  const [inscripciones, setInscripciones] = useState<MisInscripcion[]>([]);
  const [convocatoria, setConvocatoria] = useState<ConvocatoriaVigente | null>(null);
  const [tecnicatura, setTecnicatura] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [refrescando, setRefrescando] = useState(false);
  const [error, setError] = useState('');

  const cargar = useCallback(async () => {
    const tec = await leerTecnicatura();
    setTecnicatura(tec);
    if (!session) return;
    if (session.demo) {
      setMesas([]);
      setInscripciones([]);
      setConvocatoria(null);
      setError('');
      return;
    }
    try {
      const [tablas, mias] = await Promise.all([
        fetchMesasDisponibles(session.access),
        fetchMisInscripciones(session.access),
      ]);
      setMesas(tablas);
      setInscripciones(mias);
      setError('');

      // The window is optional context: without one the student still sees
      // their own enrollments, so a failure here never blanks the screen.
      try {
        setConvocatoria(await fetchConvocatoriaVigente(session.access));
      } catch {
        setConvocatoria(null);
      }
    } catch (err) {
      setMesas([]);
      setInscripciones([]);
      setConvocatoria(null);
      setError(mensajeDeError(err));
    }
  }, [session]);

  useFocusEffect(
    useCallback(() => {
      let activo = true;
      setLoading(true);
      cargar().finally(() => {
        if (activo) setLoading(false);
      });
      return () => {
        activo = false;
      };
    }, [cargar]),
  );

  const refrescar = async () => {
    setRefrescando(true);
    await cargar();
    setRefrescando(false);
  };

  // RB-02: only tables of the student's own tecnicatura.
  const propias = filtraMesasPorTecnicatura(mesas, tecnicatura);
  const visibles =
    anio === 0 ? propias : propias.filter((m) => anioDe(m.curso_nombre) === anio);
  const inscriptas = inscripciones.filter((i) => i.estado !== 'anulado');
  const total = propias.length;
  const progreso = total > 0 ? inscriptas.length / total : 0;

  return (
    <Screen edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={
          <RefreshControl refreshing={refrescando} onRefresh={refrescar} />
        }
      >
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

        {/* Progress card */}
        <LinearGradient
          colors={[...gradientPurple.colors] as [string, string]}
          locations={[...gradientPurple.locations]}
          style={styles.levelCard}
        >
          <View style={styles.levelTop}>
            <View style={{ flex: 1 }}>
              <Text style={styles.levelTitle}>
                Inscripción {Math.round(progreso * 100)}%
              </Text>
              <Text style={styles.levelSub}>
                {inscriptas.length} de {total} mesas de tu tecnicatura
              </Text>
            </View>
            <Text style={{ fontSize: 28 }}>🎓</Text>
          </View>
          <ProgressBar value={progreso} />
        </LinearGradient>

        {convocatoria ? (
          <Card style={{ gap: space(2) }}>
            <View style={styles.convRow}>
              <Text style={styles.cardTitle}>Convocatoria</Text>
              <View
                style={[
                  styles.convBadge,
                  convocatoria.activa ? styles.convOpen : styles.convClosed,
                ]}
              >
                <Text
                  style={[
                    styles.convBadgeText,
                    convocatoria.activa ? styles.convOpenText : styles.convClosedText,
                  ]}
                >
                  {convocatoria.activa ? 'Abierta' : 'Cerrada'}
                </Text>
              </View>
            </View>
            <Text style={styles.materiaName}>{convocatoria.descripcion}</Text>
            <Text style={fonts.muted}>
              Inscripción del {formatFecha(convocatoria.fecha_inicio_inscripcion)} al{' '}
              {formatFecha(convocatoria.fecha_fin_inscripcion)}
            </Text>
            {!convocatoria.activa ? (
              <Text style={[fonts.muted, { lineHeight: 20 }]}>
                La inscripción está cerrada. Podés consultar tus inscripciones abajo.
              </Text>
            ) : null}
          </Card>
        ) : null}

        {session?.demo ? (
          <Card style={{ gap: space(2) }}>
            <Text style={styles.cardTitle}>Sesión de demostración</Text>
            <Text style={[fonts.muted, { lineHeight: 20 }]}>
              El backend no está conectado. Configurá{' '}
              <Text style={styles.code}>EXPO_PUBLIC_API_BASE</Text> con la URL del
              servidor y volvé a iniciar sesión para ver las mesas reales.
            </Text>
          </Card>
        ) : null}

        {error ? (
          <Card style={{ gap: space(2) }}>
            <Text style={styles.errorTitle}>No se pudieron cargar las mesas</Text>
            <Text style={[fonts.muted, { lineHeight: 20 }]}>{error}</Text>
            <PillButton label="Reintentar" variant="ghost" onPress={refrescar} />
          </Card>
        ) : null}

        {/* Mascot header for the section */}
        {!error ? (
          <Card style={{ alignItems: 'center', paddingVertical: space(4) }}>
            <Image
              source={require('../../assets/mascots/mesas-examen.png')}
              style={{ width: 120, height: 120, borderRadius: radii.pill }}
              resizeMode="contain"
            />
            <Text style={styles.cardTitle}>Materias disponibles</Text>
            <Text style={[fonts.muted, { textAlign: 'center' }]}>
              {loading
                ? 'Cargando mesas…'
                : !tecnicatura
                  ? 'Elegí tu tecnicatura en el registro o el perfil para ver tus mesas.'
                  : total === 0
                    ? 'No hay mesas de tu tecnicatura en la convocatoria vigente.'
                    : 'Elegí una mesa para ver el detalle e inscribirte.'}
            </Text>
            {tecnicatura ? (
              <View style={styles.tecBadge}>
                <Text style={styles.tecBadgeText}>{tecnicatura}</Text>
              </View>
            ) : (
              <PillButton
                label="Elegir tecnicatura"
                variant="ghost"
                onPress={() => router.push('/(alumno)/perfil')}
              />
            )}
          </Card>
        ) : null}

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
          {visibles.length === 0 ? (
            <Text style={fonts.muted}>
              {loading ? 'Cargando…' : 'Sin materias para este filtro.'}
            </Text>
          ) : (
            visibles.map((m) => {
              const yaInscripto = inscriptas.some(
                (i) => i.materia_id === m.materia_id && i.condicion_id === m.condicion_id,
              );
              return (
                <Pressable
                  key={`${m.materia_id}-${m.condicion_id}`}
                  accessibilityRole="button"
                  accessibilityLabel={`${m.materia_nombre}, ${m.condicion_nombre}`}
                  onPress={() =>
                    router.push({
                      pathname: '/(alumno)/mesa',
                      params: {
                        materia_id: m.materia_id,
                        condicion_id: m.condicion_id,
                        materia: m.materia_nombre,
                        curso: m.curso_nombre,
                        condicion: m.condicion_nombre,
                        orientacion: m.orientacion_nombre,
                        fecha: m.fecha,
                        hora: m.hora ?? '',
                        inscripto: yaInscripto ? '1' : '0',
                      },
                    })
                  }
                  style={({ pressed }) => [styles.materiaRow, pressed && styles.pressed]}
                >
                  <View style={{ flex: 1 }}>
                    <Text style={styles.materiaName}>{m.materia_nombre}</Text>
                    <Text style={fonts.muted}>
                      {m.condicion_nombre} · {m.curso_nombre} ·{' '}
                      {formatFecha(m.fecha)} {formatHora(m.hora)}
                    </Text>
                  </View>
                  {yaInscripto ? (
                    <View style={[styles.estadoBadge, styles.estadoOk]}>
                      <Text style={[styles.estadoText, styles.estadoTextOk]}>Inscripto</Text>
                    </View>
                  ) : null}
                  <Text style={styles.chevron}>›</Text>
                </Pressable>
              );
            })
          )}
        </Card>

        {/* My enrollments */}
        <Card style={{ gap: space(3) }}>
          <Text style={styles.cardTitle}>Mis inscripciones</Text>
          {inscripciones.length === 0 ? (
            <Text style={fonts.muted}>
              {loading ? 'Cargando…' : 'Todavía no te inscribiste a ninguna mesa.'}
            </Text>
          ) : (
            inscripciones.map((i) => (
              <View key={i.id} style={styles.materiaRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.materiaName}>{i.materia_nombre}</Text>
                  <Text style={fonts.muted}>
                    {i.condicion_nombre} · {formatFecha(i.fecha)} {formatHora(i.hora)}
                  </Text>
                </View>
                <View
                  style={[
                    styles.estadoBadge,
                    i.estado === 'anulado' ? styles.estadoAnulado : styles.estadoOk,
                  ]}
                >
                  <Text
                    style={[
                      styles.estadoText,
                      i.estado === 'anulado' ? styles.estadoTextAnulado : styles.estadoTextOk,
                    ]}
                  >
                    {i.estado === 'anulado' ? 'Anulada' : 'Inscripto'}
                  </Text>
                </View>
              </View>
            ))
          )}
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
  code: {
    fontWeight: '700',
    color: colors.ink,
  },
  errorTitle: {
    ...fonts.h3,
    color: colors.danger,
  },
  chipRow: {
    gap: space(2),
    paddingVertical: space(1),
  },
  tecBadge: {
    alignSelf: 'center',
    backgroundColor: 'rgba(186, 152, 242, 0.2)',
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: colors.purple,
    paddingHorizontal: space(3),
    paddingVertical: space(1.5),
  },
  tecBadgeText: {
    color: colors.purpleDeep,
    fontSize: 12,
    fontWeight: '700',
    textAlign: 'center',
  },
  materiaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space(3),
    paddingVertical: space(1),
  },
  pressed: {
    opacity: 0.6,
  },
  materiaName: {
    fontWeight: '700',
    color: colors.ink,
    fontSize: 15,
  },
  chevron: {
    fontSize: 22,
    color: colors.purple,
    fontWeight: '700',
  },
  estadoBadge: {
    borderRadius: radii.pill,
    paddingHorizontal: space(3),
    paddingVertical: space(1.5),
  },
  estadoOk: {
    backgroundColor: 'rgba(74, 222, 128, 0.15)',
  },
  estadoAnulado: {
    backgroundColor: 'rgba(248, 113, 113, 0.15)',
  },
  estadoText: {
    fontSize: 12,
    fontWeight: '700',
  },
  estadoTextOk: {
    color: '#4ADE80',
  },
  estadoTextAnulado: {
    color: '#F87171',
  },
  convRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: space(2),
  },
  convBadge: {
    borderRadius: radii.pill,
    paddingHorizontal: space(3),
    paddingVertical: space(1.5),
  },
  convOpen: {
    backgroundColor: 'rgba(74, 222, 128, 0.15)',
  },
  convClosed: {
    backgroundColor: 'rgba(248, 113, 113, 0.15)',
  },
  convBadgeText: {
    fontSize: 12,
    fontWeight: '700',
  },
  convOpenText: {
    color: '#4ADE80',
  },
  convClosedText: {
    color: '#F87171',
  },
});
