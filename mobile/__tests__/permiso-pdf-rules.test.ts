/**
 * Exam-permit PDF rules — RED first (RB-13 cap, condition mapping,
 * date/curso helpers, validation).
 */
import { describe, expect, it } from '@jest/globals';

import {
  MAX_MATERIAS_PERMISO,
  anioDeCurso,
  fechaEmisionTexto,
  fechaMesaTexto,
  mapearCondicionImpreso,
  materiasParaImpreso,
  resolverAnio,
  tituloAlumno,
  validarDatosPermiso,
} from '../src/permisoPdfRules';

describe('permisoPdfRules — mapearCondicionImpreso', () => {
  it('mapea Regular y Previas del backend al impreso', () => {
    expect(mapearCondicionImpreso('Regular')).toBe('regular');
    expect(mapearCondicionImpreso('previa')).toBe('previa');
    expect(mapearCondicionImpreso('Previas')).toBe('previa');
  });

  it('mapea completar estudio y equivalencia', () => {
    expect(mapearCondicionImpreso('Completar Estudio')).toBe('completar_estudio');
    expect(mapearCondicionImpreso('equivalencia')).toBe('equivalencia');
  });

  it('Libre no está en el impreso → null', () => {
    expect(mapearCondicionImpreso('Libre')).toBeNull();
  });
});

describe('permisoPdfRules — tituloAlumno', () => {
  it('usa el título del impreso cuando la condición mapea', () => {
    expect(tituloAlumno('Regular')).toBe('Regular');
    expect(tituloAlumno('Previas')).toBe('Previas');
  });

  it('cae al rótulo crudo cuando no mapea', () => {
    expect(tituloAlumno('Libre')).toBe('Libre');
  });
});

describe('permisoPdfRules — fechas', () => {
  it('convierte la ISO de la mesa a DD/MM/YYYY', () => {
    expect(fechaMesaTexto('2026-12-15')).toBe('15/12/2026');
  });

  it('deja pasar valores ya formateados', () => {
    expect(fechaMesaTexto('15/12/2026')).toBe('15/12/2026');
  });

  it('arma la línea de emisión en español', () => {
    expect(fechaEmisionTexto(new Date(2026, 10, 17))).toBe(
      '17 de noviembre de 2026.',
    );
  });
});

describe('permisoPdfRules — anioDeCurso / resolverAnio', () => {
  it('extrae el año de curso_nombre', () => {
    expect(anioDeCurso('3er Año')).toBe('3');
    expect(anioDeCurso('1° Año')).toBe('1');
    expect(anioDeCurso('sin número')).toBe('');
  });

  it('resuelve el año cruzando inscripción con mesas', () => {
    const anio = resolverAnio(
      [{ materia_nombre: 'Química', fecha: '2026-12-01' }],
      [
        {
          materia_nombre: 'Física',
          fecha: '2026-12-01',
          curso_nombre: '1er Año',
        },
        {
          materia_nombre: 'Química',
          fecha: '2026-12-01',
          curso_nombre: '3er Año',
        },
      ],
    );
    expect(anio).toBe('3');
  });

  it('devuelve vacío si no hay mesa que empate', () => {
    expect(resolverAnio([{ materia_nombre: 'X', fecha: '2026-12-01' }], [])).toBe(
      '',
    );
  });
});

describe('permisoPdfRules — validarDatosPermiso (RB-13)', () => {
  const base = {
    alumno: 'PÉREZ, MARÍA',
    dni: '38456789',
    condicion: 'Regular',
    carrera: 'GESTIÓN ORGANIZACIONAL',
    anio: '3',
    materias: [{ nombre: 'Química', fecha: '2026-12-01' }],
  };

  it('acepta un payload completo', () => {
    expect(() => validarDatosPermiso(base)).not.toThrow();
  });

  it('rechaza alumno, dni, carrera o condición vacíos', () => {
    expect(() => validarDatosPermiso({ ...base, alumno: '  ' })).toThrow(
      /nombre del alumno/,
    );
    expect(() => validarDatosPermiso({ ...base, dni: '' })).toThrow(/D\.N\.I\./);
    expect(() => validarDatosPermiso({ ...base, carrera: '' })).toThrow(
      /tecnicatura/,
    );
    expect(() => validarDatosPermiso({ ...base, condicion: '' })).toThrow(
      /condición/,
    );
  });

  it('rechaza sin materias y con más de RB-13', () => {
    expect(() => validarDatosPermiso({ ...base, materias: [] })).toThrow(
      /no tiene materias/,
    );
    const muchas = Array.from({ length: MAX_MATERIAS_PERMISO + 1 }, (_, i) => ({
      nombre: `Materia ${i + 1}`,
      fecha: '2026-12-01',
    }));
    expect(() => validarDatosPermiso({ ...base, materias: muchas })).toThrow(
      /RB-13/,
    );
  });
});

describe('permisoPdfRules — materiasParaImpreso', () => {
  it('normaliza fechas y trunca a RB-13', () => {
    const muchas = Array.from({ length: 8 }, (_, i) => ({
      nombre: `M${i}`,
      fecha: '2026-12-01',
    }));
    const salida = materiasParaImpreso(muchas);
    expect(salida).toHaveLength(MAX_MATERIAS_PERMISO);
    expect(salida[0].fecha).toBe('01/12/2026');
  });
});
