/**
 * Mesa detail + inscription confirmation (S8).
 *
 * Shows the selected mesa snapshot and submits the inscription with the real
 * contract: `POST /api/v1/inscripciones` body `{ materia_id, condicion_id }`
 * (the current convocatoria is implicit, RB-30 / A-SDD4-4).
 */
import { useLocalSearchParams, useRouter } from 'expo-router';
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
  ApiError,
  apiErrorMessage,
  postInscripcion,
  type InscripcionCreada,
} from '../../src/api';
import { Card, PillButton, Screen } from '../../src/components/ui';
import { SlideToConfirm } from '../../src/components/SlideToConfirm';
import { colors, fonts, radii, space } from '../../src/theme';

type Params = {
  materia_id?: string;
  condicion_id?: string;
  materia?: string;
  curso?: string;
  condicion?: string;
  orientacion?: string;
  fecha?: string;
  hora?: string;
};

/** "2026-12-15" -> "15/12/2026". */
function formatFecha(iso?: string): string {
  if (!iso) return 'Por definir';
  const [anio, mes, dia] = iso.split('-');
  return anio && mes && dia ? `${dia}/${mes}/${anio}` : iso;
}

/** "08:00:00" -> "08:00 hs". */
function formatHora(hora?: string): string {
  if (!hora) return 'A confirmar';
  return `${hora.slice(0, 5)} hs`;
}

export default function MesaDetalle() {
  const router = useRouter();
  const params = useLocalSearchParams<Params>();
  const { session } = useAuth();
  const [confirmada, setConfirmada] = useState<InscripcionCreada | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState('');

  const materia = params.materia ?? 'Materia';
  const curso = params.curso ?? '—';
  const condicion = params.condicion ?? '—';
  const orientacion = params.orientacion ?? '—';
  const fecha = formatFecha(params.fecha);
  const hora = formatHora(params.hora);

  const inscribir = async () => {
    if (enviando) return;
    setError('');

    if (!session || session.demo) {
      setError(
        'Necesitás una sesión real para inscribirte. Conectá el backend y volvé a entrar.',
      );
      return;
    }
    if (!params.materia_id || !params.condicion_id) {
      setError('Esta mesa no vino del listado del servidor: volvé al inicio y elegila de nuevo.');
      return;
    }

    setEnviando(true);
    try {
      const creada = await postInscripcion(session.access, {
        materia_id: params.materia_id,
        condicion_id: params.condicion_id,
      });
      setConfirmada(creada);
    } catch (err) {
      if (err instanceof ApiError) {
        switch (err.code) {
          case 'ventana-cerrada':
            setError('La ventana de inscripción está cerrada.');
            break;
          case 'inscripcion-duplicada':
            setError('Ya estás inscripto en esta materia para la convocatoria vigente.');
            break;
          case 'limite-materias':
            setError('Alcanzaste el límite de materias para tu condición.');
            break;
          case 'mesa-no-disponible':
            setError('Esta mesa ya no está disponible. Volvé al inicio y recargá el listado.');
            break;
          case 'convocatoria-no-encontrada':
            setError('No hay una convocatoria de exámenes publicada.');
            break;
          case 'materia-no-encontrada':
          case 'condicion-no-encontrada':
            setError('La materia o la condición ya no está activa en el sistema.');
            break;
          default:
            setError(apiErrorMessage(err, 'No se pudo completar la inscripción.'));
        }
      } else {
        setError('No se pudo conectar con el servidor. Revisá tu conexión e intentá de nuevo.');
      }
    } finally {
      setEnviando(false);
    }
  };

  return (
    <Screen edges={['top', 'bottom']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.headerRow}>
          <PillButton
            label=""
            variant="subtle"
            onPress={() => router.back()}
            style={styles.backBtn}
          />
          <View style={{ flex: 1 }}>
            <Text style={fonts.h1}>Detalle de mesa</Text>
            <Text style={fonts.muted}>Revisá los datos antes de inscribirte</Text>
          </View>
        </View>

        <Card style={{ alignItems: 'center', paddingVertical: space(5) }}>
          <Image
            source={require('../../assets/mascots/mesas-examen.png')}
            style={{ width: 130, height: 130, borderRadius: radii.pill }}
            resizeMode="contain"
          />
          <Text style={styles.materiaName}>{materia}</Text>
          <Text style={fonts.muted}>{curso}</Text>
        </Card>

        <Card style={{ gap: space(3) }}>
          <Text style={fonts.h3}>Datos de la mesa</Text>
          <Row label="Condición" value={condicion} />
          <Row label="Orientación" value={orientacion} />
          <Row label="Fecha" value={fecha} />
          <Row label="Hora" value={hora} />
          <Row label="Estado" value={confirmada ? 'Inscripto' : 'Disponible'} accent={!!confirmada} />
        </Card>

        <Card style={{ gap: space(3) }}>
          <Text style={fonts.h3}>Condiciones</Text>
          <Text style={[fonts.muted, { lineHeight: 20 }]}>
            Al inscribirte confirmás que cumplís las condiciones de la mesa
            (RB-18). La inscripción es definitiva una vez aprobada por el
            sistema del colegio.
          </Text>
        </Card>

        {confirmada ? (
          <Card style={{ alignItems: 'center', gap: space(2) }}>
            <Text style={{ fontSize: 40 }}>✅</Text>
            <Text style={fonts.h3}>Inscripción registrada</Text>
            <Text style={[fonts.muted, { textAlign: 'center' }]}>
              Quedaste inscripto en {confirmada.estado === 'inscripto' ? 'la mesa' : 'la mesa'}{' '}
              de {materia}. El sistema del colegio la aprobará y vas a recibir
              el permiso de examen.
            </Text>
            <PillButton
              label="Volver al inicio"
              variant="ghost"
              onPress={() => router.replace('/(alumno)/inicio')}
            />
          </Card>
        ) : (
          <>
            <SlideToConfirm
              label={enviando ? 'Enviando inscripción…' : 'Deslizá para inscribirte'}
              onConfirm={inscribir}
              disabled={enviando}
            />
            {error ? <Text style={styles.error}>{error}</Text> : null}
          </>
        )}

        <View style={{ height: space(10) }} />
      </ScrollView>
    </Screen>
  );
}

function Row({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <View style={styles.row}>
      <Text style={fonts.muted}>{label}</Text>
      <Text
        style={[
          styles.rowValue,
          accent && { color: colors.success },
        ]}
      >
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  scroll: {
    padding: space(5),
    gap: space(4),
    paddingBottom: space(6),
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space(3),
  },
  backBtn: {
    minHeight: 40,
    minWidth: 40,
    paddingHorizontal: space(3),
  },
  materiaName: {
    ...fonts.h2,
    textAlign: 'center',
    marginTop: space(2),
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: space(3),
    paddingVertical: space(1),
  },
  rowValue: {
    fontWeight: '600',
    color: colors.ink,
    fontSize: 14,
    flexShrink: 1,
    textAlign: 'right',
  },
  error: {
    color: colors.danger,
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 19,
  },
});
