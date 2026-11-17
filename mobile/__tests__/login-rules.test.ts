/**
 * Login gate rules (RED first): the slider must not complete unless both
 * identifiers are present, and the failure must be recoverable.
 */
import { describe, expect, it } from '@jest/globals';

import { loginListo, etiquetaSlider } from '../src/loginRules';

describe('login gate', () => {
  it('no deja deslizar sin usuario', () => {
    expect(loginListo('', 'secreta')).toBe(false);
  });

  it('no deja deslizar sin contraseña', () => {
    expect(loginListo('alumno01', '')).toBe(false);
  });

  it('no deja deslizar con solo espacios', () => {
    expect(loginListo('   ', '   ')).toBe(false);
  });

  it('deja deslizar con usuario y contraseña', () => {
    expect(loginListo('alumno01', 'secreta')).toBe(true);
  });

  it('avisa qué falta mientras no está completo', () => {
    expect(etiquetaSlider('', '', false)).toBe('Completá usuario y contraseña');
    expect(etiquetaSlider('alumno01', '', false)).toBe('Completá usuario y contraseña');
  });

  it('muestra el estado de ingreso mientras espera', () => {
    expect(etiquetaSlider('alumno01', 'secreta', true)).toBe('Ingresando…');
  });

  it('vuelve al texto normal cuando ya está completo', () => {
    expect(etiquetaSlider('alumno01', 'secreta', false)).toBe('Deslizá para iniciar sesión');
  });
});