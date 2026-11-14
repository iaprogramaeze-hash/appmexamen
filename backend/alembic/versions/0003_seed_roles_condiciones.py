"""0003: semilla de roles + matriz rol×permiso (PD-03) y condiciones (PD-02)

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-22

PD-03 [CERRADO 2026-10-06]: "los roles y los permisos viajan en la
migración inicial de Alembic (datos estáticos, reproducibles en dev,
staging y prod)". Los 13 permisos y 3 módulos ya los creó 0001; esta
revisión agrega los 5 roles de la matriz doc02 §2.4 y su asignación
rol × permiso EXACTA: celda `S` asigna; celda `—` o `PENDIENTE` no
asigna (un hueco de la matriz nunca otorga permiso). `preinscripcion.crear`
no se asigna a ningún rol (G-02).

PD-02 [CERRADO 2026-10-06]: "los valores de es_condicion.limite_materias
se siembran como default (Previa 3, Regular 8, Libre NULL) y quedan
editables desde SIGME".

Idempotente: toda inserción usa ON CONFLICT DO NOTHING. Data inline
(la migración no importa código de app/).
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

#: §2.4 — columnas S de la matriz (DEFINITIVA, fuente de la semilla PD-03).
#: Formato: (rol, permiso).
_MATRIZ: tuple[tuple[str, str], ...] = (
    # alumno
    ("alumno", "mesa.listar"),
    ("alumno", "inscripcion.listar"),
    ("alumno", "inscripcion.crear"),
    ("alumno", "inscripcion.anular"),
    # secretario
    ("secretario", "mesa.listar"),
    ("secretario", "mesa.crear"),
    ("secretario", "mesa.modificar"),
    ("secretario", "inscripcion.listar"),
    ("secretario", "inscripcion.anular"),
    ("secretario", "persona.listar"),
    ("secretario", "persona.modificar"),
    ("secretario", "reporte.exportar"),
    ("secretario", "preinscripcion.listar"),
    # director
    ("director", "mesa.listar"),
    ("director", "inscripcion.listar"),
    ("director", "persona.listar"),
    ("director", "reporte.exportar"),
    ("director", "preinscripcion.listar"),
    # administrador (todos salvo preinscripcion.crear — G-02)
    ("administrador", "mesa.listar"),
    ("administrador", "mesa.crear"),
    ("administrador", "mesa.modificar"),
    ("administrador", "mesa.eliminar"),
    ("administrador", "inscripcion.listar"),
    ("administrador", "inscripcion.crear"),
    ("administrador", "inscripcion.anular"),
    ("administrador", "persona.listar"),
    ("administrador", "persona.modificar"),
    ("administrador", "usuario.gestionar"),
    ("administrador", "reporte.exportar"),
    ("administrador", "preinscripcion.listar"),
    # superadmin (mismo reparto que administrador; la diferencia efectiva
    # de funciones sigue PENDIENTE en doc02 §2.3)
    ("superadmin", "mesa.listar"),
    ("superadmin", "mesa.crear"),
    ("superadmin", "mesa.modificar"),
    ("superadmin", "mesa.eliminar"),
    ("superadmin", "inscripcion.listar"),
    ("superadmin", "inscripcion.crear"),
    ("superadmin", "inscripcion.anular"),
    ("superadmin", "persona.listar"),
    ("superadmin", "persona.modificar"),
    ("superadmin", "usuario.gestionar"),
    ("superadmin", "reporte.exportar"),
    ("superadmin", "preinscripcion.listar"),
)

#: §3.6 — los 5 roles (columnas de la matriz §2.4).
_ROLES: tuple[tuple[str, str], ...] = (
    ("alumno", "Alumno (SIGME-M)"),
    ("secretario", "Secretario/a"),
    ("director", "Director"),
    ("administrador", "Administrador"),
    ("superadmin", "Superadmin"),
)

#: PD-02 — (descripcion, limite_materias); NULL = sin límite.
_CONDICIONES: tuple[tuple[str, int | None], ...] = (
    ("Previa", 3),
    ("Regular", 8),
    ("Libre", None),
)


def upgrade() -> None:
    # 1) Roles (§3.6): codigo UNIQUE → ON CONFLICT (codigo) DO NOTHING.
    valores_roles = ",\n    ".join(
        f"('{codigo}', '{descripcion}')" for codigo, descripcion in _ROLES
    )
    op.execute(
        f"""INSERT INTO us_rol (codigo, descripcion)
VALUES
    {valores_roles}
ON CONFLICT (codigo) DO NOTHING;"""
    )

    # 2) Matriz rol × permiso: cada par se resuelve por código a los ids.
    #    PK compuesta (rol_id, permiso_id) → ON CONFLICT DO NOTHING plano.
    valores_matriz = ",\n    ".join(
        f"('{rol}', '{permiso}')" for rol, permiso in _MATRIZ
    )
    op.execute(
        f"""INSERT INTO us_rol_permiso (rol_id, permiso_id)
SELECT r.id, p.id
FROM (VALUES
    {valores_matriz}
) AS t(rol_codigo, permiso_codigo)
JOIN us_rol r ON r.codigo = t.rol_codigo
JOIN us_permiso p ON p.codigo = t.permiso_codigo
ON CONFLICT DO NOTHING;"""
    )

    # 3) Condiciones (PD-02): descripcion UNIQUE → ON CONFLICT (descripcion).
    valores_condiciones = ",\n    ".join(
        f"('{descripcion}', {limite if limite is not None else 'NULL'})"
        for descripcion, limite in _CONDICIONES
    )
    op.execute(
        f"""INSERT INTO es_condicion (descripcion, limite_materias)
VALUES
    {valores_condiciones}
ON CONFLICT (descripcion) DO NOTHING;"""
    )


def downgrade() -> None:
    # Semilla estática: el downgrade retira exactamente lo que insertó esta
    # revisión, sin tocar datos que un operador haya creado después.
    op.execute(
        """DELETE FROM us_rol_permiso
WHERE (rol_id, permiso_id) IN (
    SELECT r.id, p.id
    FROM (VALUES
"""
        + ",\n".join(
            f"    ('{rol}', '{permiso}')" for rol, permiso in _MATRIZ
        )
        + """
    ) AS t(rol_codigo, permiso_codigo)
    JOIN us_rol r ON r.codigo = t.rol_codigo
    JOIN us_permiso p ON p.codigo = t.permiso_codigo
);"""
    )
    roles_codigos = ", ".join(f"'{codigo}'" for codigo, _ in _ROLES)
    op.execute(f"DELETE FROM us_rol WHERE codigo IN ({roles_codigos})")
    condiciones = ", ".join(f"'{desc}'" for desc, _ in _CONDICIONES)
    op.execute(f"DELETE FROM es_condicion WHERE descripcion IN ({condiciones})")
