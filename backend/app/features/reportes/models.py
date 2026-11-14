"""Modelos de reportes (SDD-5).

Los reportes NO definen nuevas tablas; usan las existentes:
- es_mesa_examen (con snapshots RB-11)
- es_mesa_inscripcion (inscripciones activas)
- es_convocatoria
- es_grupo_horario
- us_usuario
- pe_persona (para documento en acta volante)

Este archivo existe solo para que el conftest pueda importar el módulo
y registrar cualquier modelo futuro si se añade.
"""
from __future__ import annotations

# Sin modelos propios por ahora; reutiliza esquemas existentes.
# Si en el futuro se añade una tabla de auditoría de reportes (PD-05),
# se definirá aquí.