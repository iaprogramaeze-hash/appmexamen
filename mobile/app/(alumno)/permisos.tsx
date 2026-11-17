/**
 * Student permits (permiso de examen) — S8/S13.
 *
 * Lists the student's active enrollments grouped by condition (RB-18:
 * one permiso per condition; mixed conditions → two permisos). The PDF is
 * generated on-device with our school template (not the backend; the
 * colleague only provides the enrolled subjects via `GET /mis-inscripciones`).
 */
import { useFocusEffect } from 'expo-router';
import React, { useCallback, useState } from 'react';
import { Image, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import { useAuth } from '../../src/auth';
import { ApiError, apiErrorMessage, fetchMisInscripciones, type MisInscripcion } from '../../src/api';
import { Card, PillButton, Screen } from '../../src/components/ui';
import { agrupaPorCondicion } from '../../src/permisoRules';
import { colors, fonts, radii, space } from '../../src/theme';

/** "2026-12-15" -> "15/12". */
function formatFecha(iso: string): string {
  const [, mes, dia] = iso.split('-');
  return mes && dia ? `${dia}/${mes}` : iso;
}

/** "08:00:00" -> "08:00". */
function formatHora(hora: string | null): string {
  return hora ? hora.slice(0, 5) : '—';
}

export default function Permisos() {
  const { session } = useAuth();
  const [inscripciones, setInscripciones] = useState<MisInscripcion[]>([]);
  const [loading, setLoading] = useState(false);
  const [refrescando, setRefrescando] = useState(false);
  const [error, setError] = useState('');

  const cargar = useCallback(async () => {
    if (!session) return;
    if (session.demo) {
      setInscripciones([]);
      setError('');
      return;
    }
    try {
      const filas = await fetchMisInscripciones(session.access);
      setInscripciones(filas);
      setError('');
    } catch (err) {
      setInscripciones([]);
      if (err instanceof ApiError) setError(apiErrorMessage(err, 'No se pudieron cargar tus permisos.'));
      else setError('No se pudo conectar con el servidor.');
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

  const grupos = agrupaPorCondicion(inscripciones);

  return (
    <Screen edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={refrescando} onRefresh={refrescar} />}
      >
        <View>
          <Text style={fonts.h1}>Mis permisos</Text>
          <Text style={fonts.muted}>
            Permisos de examen de tus inscripciones (RB-18)
          </Text>
        </View>

        {error ? (
          <Card style={{ gap: space(2) }}>
            <Text style={styles.errorTitle}>No se pudieron cargar los permisos</Text>
            <Text style={[fonts.muted, { lineHeight: 20 }]}>{error}</Text>
            <PillButton label="Reintentar" variant="ghost" onPress={refrescar} />
          </Card>
        ) : null}

        {session?.demo ? (
          <Card style={{ gap: space(2) }}>
            <Text style={fonts.h3}>Sesión de demostración</Text>
            <Text style={[fonts.muted, { lineHeight: 20 }]}>
              El backend no está conectado. Inicia sesión con el servidor levantado
              para ver tus permisos reales.
            </Text>
          </Card>
        ) : null}

        {!loading && !error && grupos.length === 0 ? (
          <Card style={{ alignItems: 'center', paddingVertical: space(5) }}>
            <Image
              source={require('../../assets/mascots/tatu-estudia.png')}
              style={{ width: 140, height: 140, borderRadius: radii.pill }}
              resizeMode="contain"
            />
            <Text style={styles.title}>Tus permisos aparecen acá</Text>
            <Text style={[fonts.muted, { textAlign: 'center' }]}>
              Cuando te inscribas a una mesa, el permiso de examen se arma con
              tus materias (RB-18).
            </Text>
          </Card>
        ) : null}

        {grupos.map((g) => (
          <Card key={g.condicion} style={{ gap: space(3) }}>
            <View style={styles.grupoHead}>
              <Text style={fonts.h3}>Permiso · {g.condicion}</Text>
              <Text style={styles.badge}>{g.items.length} {g.items.length === 1 ? 'materia' : 'materias'}</Text>
            </View>
            {g.items.map((m, idx) => (
              <View key={`${m.materia_nombre}-${idx}`} style={styles.materiaRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.materiaName}>{m.materia_nombre}</Text>
                  <Text style={fonts.muted}>
                    {formatFecha(m.fecha)} · {formatHora(m.hora)}
                  </Text>
                </View>
              </View>
            ))}
            <PillButton label="Descargar PDF del permiso" withArrow disabled />
            <Text style={[fonts.muted, { textAlign: 'center', fontSize: 12 }]}>
              El PDF se genera en tu celular con la plantilla de la escuela
              (no se guarda en el servidor).
            </Text>
          </Card>
        ))}

        <Card>
          <Text style={fonts.h3}>Cómo funcionan</Text>
          <Text style={[fonts.muted, { lineHeight: 20 }]}>
            Cada grupo de condiciones genera su permiso (RB-18). El límite de
            materias es por condición (RB-03): Previa hasta 3, Regular hasta 8.
            LIBRO/FOLIO los carga la escuela. El PDF es borrador: solo vale con
            la firma manuscrita del Secretario.
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
  errorTitle: {
    ...fonts.h3,
    color: colors.danger,
  },
  grupoHead: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: space(2),
  },
  badge: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.purpleDeep,
    backgroundColor: 'rgba(186, 152, 242, 0.2)',
    borderRadius: radii.pill,
    paddingHorizontal: space(2),
    paddingVertical: space(1),
    overflow: 'hidden',
  },
  materiaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space(3),
    paddingVertical: space(1),
  },
  materiaName: {
    fontWeight: '700',
    color: colors.ink,
    fontSize: 15,
  },
});
