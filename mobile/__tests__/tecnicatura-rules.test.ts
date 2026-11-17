/**
 * RB-02 (RED first): one tecnicatura per student; the enrollment list must
 * only show tables of that tecnicatura, never another career's.
 */
import { describe, expect, it } from '@jest/globals';

import {
  TECNICATURAS,
  esTecnicatura,
  filtraMesasPorTecnicatura,
} from '../src/tecnicaturaRules';

const mesa = (orientacion_nombre: string, materia = 'Materia') => ({
  orientacion_nombre,
  materia_nombre: materia,
});

describe('catálogo de tecnicaturas', () => {
  it('ofrece exactamente las dos tecnicaturas de la escuela', () => {
    expect(TECNICATURAS).toEqual([
      'TECNOLOGÍA DE LOS ALIMENTOS',
      'GESTIÓN ORGANIZACIONAL',
    ]);
  });

  it('reconoce solo las dos oficiales', () => {
    expect(esTecnicatura('TECNOLOGÍA DE LOS ALIMENTOS')).toBe(true);
    expect(esTecnicatura('GESTIÓN ORGANIZACIONAL')).toBe(true);
    expect(esTecnicatura('Otra Carrera')).toBe(false);
    expect(esTecnicatura('')).toBe(false);
  });
});

describe('filtro RB-02 por tecnicatura del alumno', () => {
  const mesas = [
    mesa('TECNOLOGÍA DE LOS ALIMENTOS', 'Química'),
    mesa('GESTIÓN ORGANIZACIONAL', 'Contabilidad'),
    mesa('TECNOLOGÍA DE LOS ALIMENTOS', 'Microbiología'),
  ];

  it('devuelve solo las mesas de la tecnicatura del alumno', () => {
    const vistas = filtraMesasPorTecnicatura(mesas, 'GESTIÓN ORGANIZACIONAL');
    expect(vistas).toHaveLength(1);
    expect(vistas[0].materia_nombre).toBe('Contabilidad');
  });

  it('cambia el listado al cambiar la tecnicatura (una sola por alumno)', () => {
    const vistas = filtraMesasPorTecnicatura(mesas, 'TECNOLOGÍA DE LOS ALIMENTOS');
    expect(vistas.map((m) => m.materia_nombre)).toEqual([
      'Química',
      'Microbiología',
    ]);
  });

  it('sin tecnicatura no muestra ninguna mesa (no filtra al revés)', () => {
    expect(filtraMesasPorTecnicatura(mesas, null)).toEqual([]);
    expect(filtraMesasPorTecnicatura(mesas, undefined)).toEqual([]);
    expect(filtraMesasPorTecnicatura(mesas, '')).toEqual([]);
  });

  it('ignora una tecnicatura desconocida en vez de mostrar todo', () => {
    expect(filtraMesasPorTecnicatura(mesas, 'Ingeniería')).toEqual([]);
  });

  it('compara el nombre exacto del snapshot de la mesa', () => {
    const otras = filtraMesasPorTecnicatura(mesas, 'TECNOLOGÍA DE LOS ALIMENTOS ');
    expect(otras).toEqual([]);
  });
});
