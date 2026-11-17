/**
 * Permiso de examen (RB-18 / RB-03): RED first — active enrollments only,
 * grouped one-per-condition (mixed conditions → two permisos).
 */
import { describe, expect, it } from '@jest/globals';

import { agrupaPorCondicion, inscripcionesActivas } from '../src/permisoRules';

const ins = (
  condicion_nombre: string,
  materia_nombre: string,
  estado = 'inscripto',
) => ({ condicion_nombre, materia_nombre, estado, fecha: '2026-12-01', hora: '08:00:00' });

describe('permiso de examen — inscripciones activas', () => {
  it('descarta las anuladas', () => {
    const lista = [ins('Regular', 'Química'), ins('Regular', 'Física', 'anulado')];
    expect(inscripcionesActivas(lista).map((i) => i.materia_nombre)).toEqual(['Química']);
  });
});

describe('permiso de examen — RB-18 agrupación por condición', () => {
  it('una sola condición genera un solo permiso', () => {
    const grupos = agrupaPorCondicion([
      ins('Regular', 'Química'),
      ins('Regular', 'Microbiología'),
    ]);
    expect(grupos).toHaveLength(1);
    expect(grupos[0].condicion).toBe('Regular');
    expect(grupos[0].items).toHaveLength(2);
  });

  it('condiciones distintas generan dos permisos', () => {
    const grupos = agrupaPorCondicion([
      ins('Regular', 'Química'),
      ins('Previas', 'Lengua'),
      ins('Regular', 'Física'),
    ]);
    expect(grupos).toHaveLength(2);
    expect(grupos[0].condicion).toBe('Regular');
    expect(grupos[0].items).toHaveLength(2);
    expect(grupos[1].condicion).toBe('Previas');
    expect(grupos[1].items).toHaveLength(1);
  });

  it('no agrupa anuladas en ningún permiso', () => {
    const grupos = agrupaPorCondicion([
      ins('Regular', 'Química'),
      ins('Regular', 'Química', 'anulado'),
      ins('Previas', 'Lengua', 'anulado'),
    ]);
    expect(grupos).toHaveLength(1);
    expect(grupos[0].items).toHaveLength(1);
  });

  it('sin inscripciones activas no hay permisos', () => {
    expect(agrupoVacio()).toEqual([]);
  });
});

function agrupoVacio() {
  return agrupaPorCondicion([]);
}
