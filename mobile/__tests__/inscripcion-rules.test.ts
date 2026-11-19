import { describe, expect, it } from '@jest/globals';

import { puedeDarDeBaja } from '../src/inscripcionRules';

describe('puedeDarDeBaja (S15: solo hasta el día anterior a la mesa)', () => {
  // 2026-11-19 en horario local (referente inyectado para que el test no
  // dependa del día en que se ejecute).
  const hoy = new Date(2026, 10, 19);

  it('permite la baja el día anterior a la mesa', () => {
    expect(puedeDarDeBaja('2026-11-20', hoy)).toBe(true);
  });

  it('permite la baja con más de un día de anticipación', () => {
    expect(puedeDarDeBaja('2026-12-15', hoy)).toBe(true);
  });

  it('no permite la baja el mismo día de la mesa', () => {
    expect(puedeDarDeBaja('2026-11-19', hoy)).toBe(false);
  });

  it('no permite la baja cuando la mesa ya pasó', () => {
    expect(puedeDarDeBaja('2026-11-18', hoy)).toBe(false);
  });

  it('rechaza fechas malformadas o imposibles', () => {
    expect(puedeDarDeBaja('mañana', hoy)).toBe(false);
    expect(puedeDarDeBaja('2026-13-40', hoy)).toBe(false);
    expect(puedeDarDeBaja('2026-02-30', hoy)).toBe(false);
    expect(puedeDarDeBaja('', hoy)).toBe(false);
  });
});
