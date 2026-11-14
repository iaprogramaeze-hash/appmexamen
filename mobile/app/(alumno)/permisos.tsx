/**
 * Student permits (permisos de examen) — read-only view of generated permits.
 * Data comes from the backend once available; static structure mirrors the
 * prototype's permisos table (S8).
 */
import React from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { Card, Chip, Screen } from '../../src/components/ui';
import { colors, fonts, radii, space } from '../../src/theme';

type Permiso = {
  materia: string;
  fecha: string;
  condicion: string;
  libro: string;
  estado: 'vigente' | 'usado';
};

const PERMISOS: Permiso[] = [
  { materia: 'Administración y Gestión de RRHH', fecha: '10/11/2026', condicion: 'REGULAR', libro: '—', estado: 'vigente' },
  { materia: 'Comunicación y Comportamiento Org.', fecha: '11/11/2026', condicion: 'PREVIA', libro: '—', estado: 'vigente' },
  { materia: 'Tecnología de la Información y Com. 3', fecha: '13/11/2026', condicion: 'REGULAR', libro: '—', estado: 'vigente' },
  { materia: 'Sistema de Información Contable 1', fecha: '05/11/2026', condicion: 'REGULAR', libro: '—', estado: 'vigente' },
];

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

        <Card style={{ gap: space(4) }}>
          {PERMISOS.map((p) => (
            <View key={p.materia} style={styles.row}>
              <View style={{ flex: 1, gap: 4 }}>
                <Text style={styles.nombre}>{p.materia}</Text>
                <Text style={fonts.muted}>
                  {p.fecha} · Libro {p.libro}
                </Text>
              </View>
              <View style={styles.tags}>
                <View style={styles.chipCond}>
                  <Text style={styles.chipCondText}>{p.condicion}</Text>
                </View>
                <Chip label={p.estado} active={p.estado === 'vigente'} />
              </View>
            </View>
          ))}
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
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space(3),
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
    paddingBottom: space(3),
  },
  nombre: {
    fontWeight: '700',
    fontSize: 14,
    color: colors.ink,
  },
  tags: {
    gap: space(1.5),
    alignItems: 'flex-end',
  },
  chipCond: {
    backgroundColor: colors.surfaceSoft,
    borderRadius: radii.pill,
    paddingHorizontal: space(3),
    paddingVertical: space(1),
    borderWidth: 1,
    borderColor: colors.purple,
  },
  chipCondText: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.purpleDeep,
  },
});
