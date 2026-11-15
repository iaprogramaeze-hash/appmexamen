/**
 * Mesa detail + inscription confirmation (S8).
 * Shows the selected subject's exam mesa details and a slide-to-confirm
 * to submit the inscription. Skeleton until the backend exposes data.
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

import { Card, PillButton, Screen } from '../../src/components/ui';
import { SlideToConfirm } from '../../src/components/SlideToConfirm';
import { colors, fonts, radii, space } from '../../src/theme';

type Params = {
  materia?: string;
  anio?: string;
  dia?: string;
  hora?: string;
  aula?: string;
};

export default function MesaDetalle() {
  const router = useRouter();
  const params = useLocalSearchParams<Params>();
  const [confirmada, setConfirmada] = useState(false);

  const materia = params.materia ?? 'Materia';
  const anio = params.anio ?? '—';
  const dia = params.dia ?? 'Por definir';
  const hora = params.hora ?? '—';
  const aula = params.aula ?? 'Por asignar';

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
          <Text style={fonts.muted}>Año {anio}</Text>
        </Card>

        <Card style={{ gap: space(3) }}>
          <Text style={fonts.h3}>Datos de la mesa</Text>
          <Row label="Día" value={dia} />
          <Row label="Hora" value={hora} />
          <Row label="Aula" value={aula} />
          <Row label="Estado" value="Disponible" accent />
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
            <Text style={fonts.h3}>Inscripción enviada</Text>
            <Text style={[fonts.muted, { textAlign: 'center' }]}>
              Tu inscripción quedó registrada. El sistema del colegio la
              aprobará y vas a recibir el permiso de examen.
            </Text>
            <PillButton
              label="Volver al inicio"
              variant="ghost"
              onPress={() => router.replace('/(alumno)/inicio')}
            />
          </Card>
        ) : (
          <SlideToConfirm
            label="Deslizá para inscribirte"
            onConfirm={() => setConfirmada(true)}
          />
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
});
