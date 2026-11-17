/**
 * Identity helpers for the permit (nombre + DNI). AsyncStorage is mocked
 * so the pure formatter runs under Node/jest without the native module.
 */
import { describe, expect, it, jest } from '@jest/globals';

jest.mock('@react-native-async-storage/async-storage', () => ({
  __esModule: true,
  default: {
    getItem: jest.fn(async () => null),
    setItem: jest.fn(async () => undefined),
    removeItem: jest.fn(async () => undefined),
  },
}));

import { formatoAlumnoImpreso } from '../src/identidad';

describe('identidad — formatoAlumnoImpreso', () => {
  it('arma APELLIDO, NOMBRE como el impreso', () => {
    expect(
      formatoAlumnoImpreso({
        nombre: 'María Soledad',
        apellido: 'Pérez',
        dni: '38456789',
      }),
    ).toBe('Pérez, María Soledad');
  });

  it('recorta espacios sobrantes', () => {
    expect(
      formatoAlumnoImpreso({
        nombre: '  Juan  ',
        apellido: ' Gómez ',
        dni: '30',
      }),
    ).toBe('Gómez, Juan');
  });
});
