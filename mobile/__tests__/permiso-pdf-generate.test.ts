/**
 * End-to-end PDF assembly against the real school template (Node/jest).
 * Proves the output is a non-empty PDF document (RB-09: bytes only).
 */
import { describe, expect, it } from '@jest/globals';
import { readFileSync } from 'fs';
import { join } from 'path';

import { generarPermisoPdf } from '../src/permisoPdf';

const PLANTILLA = readFileSync(
  join(__dirname, '../assets/permiso-plantilla.pdf'),
);

describe('generarPermisoPdf — plantilla real', () => {
  it('devuelve un PDF con el encabezado %PDF-', async () => {
    const bytes = await generarPermisoPdf(
      {
        alumno: 'PÉREZ, MARÍA SOLEDAD',
        dni: '38.456.789',
        condicion: 'Regular',
        carrera: 'GESTIÓN ORGANIZACIONAL',
        anio: '3',
        materias: [
          { nombre: 'Química', fecha: '2026-12-01' },
          { nombre: 'Microbiología', fecha: '2026-12-03' },
        ],
        fechaEmision: new Date(2026, 10, 17),
      },
      PLANTILLA,
    );
    expect(bytes.length).toBeGreaterThan(1000);
    const head = String.fromCharCode(...bytes.subarray(0, 5));
    expect(head).toBe('%PDF-');
    // Trailer must close with %%EOF.
    const tail = String.fromCharCode(...bytes.subarray(bytes.length - 32));
    expect(tail).toContain('%%EOF');
  });

  it('acepta condición Libre (no está en el impreso, sale como texto)', async () => {
    const bytes = await generarPermisoPdf(
      {
        alumno: 'GÓMEZ, JUAN',
        dni: '30111222',
        condicion: 'Libre',
        carrera: 'TECNOLOGÍA DE LOS ALIMENTOS',
        anio: '2',
        materias: [{ nombre: 'Lengua', fecha: '2026-12-05' }],
      },
      PLANTILLA,
    );
    expect(String.fromCharCode(...bytes.subarray(0, 5))).toBe('%PDF-');
  });

  it('lanza RB-13 con más de 6 materias', async () => {
    const materias = Array.from({ length: 7 }, (_, i) => ({
      nombre: `Materia ${i + 1}`,
      fecha: '2026-12-01',
    }));
    await expect(
      generarPermisoPdf(
        {
          alumno: 'A, B',
          dni: '1',
          condicion: 'Regular',
          carrera: 'X',
          anio: '1',
          materias,
        },
        PLANTILLA,
      ),
    ).rejects.toThrow(/RB-13/);
  });
});
