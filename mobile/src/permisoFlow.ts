/**
 * Shared permit-PDF flow (S13/S15): identity + school template + share
 * sheet, used by both Permisos and Inscripción so the generation lives in
 * exactly one place (RB-09: built on the device, never uploaded).
 *
 * Throws `Error` with a user-facing Spanish message on failure; callers
 * surface it as their screen notice.
 */
import { fetchMesasDisponibles } from './api';
import { formatoAlumnoImpreso, leerIdentidad } from './identidad';
import { generarPermisoPdf } from './permisoPdf';
import type { GrupoPermiso } from './permisoRules';
import { resolverAnio } from './permisoPdfRules';
import { cargarPlantillaPermiso, compartirPdf } from './permisoShare';
import { leerTecnicatura } from './tecnicatura';

/** "Condición X" -> "condicion-x" (safe PDF file name). */
export function slugCondicion(condicion: string): string {
  return (
    condicion
      .toLowerCase()
      .normalize('NFD')
      .replace(/[̀-ͯ]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '') || 'permiso'
  );
}

/**
 * Builds the permit PDF for one condition group and opens the share sheet.
 *
 * @param grupo condition group (RB-18: one permit per condition)
 * @param accessToken student token to resolve the year, or null to skip it
 */
export async function generarPermisoParaGrupo(
  grupo: GrupoPermiso,
  accessToken: string | null,
): Promise<void> {
  const identidad = await leerIdentidad();
  const carrera = await leerTecnicatura();
  if (!identidad || !carrera) {
    throw new Error(
      'Faltan datos del permiso. Completá nombre, D.N.I. y tecnicatura en tu perfil (o creá la cuenta de nuevo).',
    );
  }

  let anio = '';
  if (accessToken) {
    try {
      const mesas = await fetchMesasDisponibles(accessToken);
      anio = resolverAnio(grupo.items, mesas);
    } catch {
      // Year is optional: the form still prints without the number.
    }
  }

  const plantilla = await cargarPlantillaPermiso();
  const bytes = await generarPermisoPdf(
    {
      alumno: formatoAlumnoImpreso(identidad),
      dni: identidad.dni,
      condicion: grupo.condicion,
      carrera,
      anio,
      materias: grupo.items.map((i) => ({
        nombre: i.materia_nombre,
        fecha: i.fecha,
      })),
    },
    plantilla,
  );
  await compartirPdf(bytes, `permiso-${slugCondicion(grupo.condicion)}.pdf`);
}
