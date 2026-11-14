"""initial: esquema completo de analisis.txt §3

Revision ID: 0001
Revises:
Create Date: 2026-10-12

Generado desde analisis.txt §3 (fuente de verdad): 22 tablas + índices +
comentarios de columna + 2 vistas + función/trigger trg_set_updated_at (§1.6).
Orden respetando FK: es_grupo_horario (§3.22) antes que es_mesa_examen
(§3.18); las vistas van después de todas las tablas.
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) función de auditoría §1.6
    op.execute(
        """-- analisis.txt 1.6 [CORREGIDO]: updated_at NO puede vivir en DEFAULT porque
-- DEFAULT sólo se evalúa al INSERT y la columna queda congelada. El trigger la
-- refresca en cada UPDATE, para cualquier cliente (API, migraciones, SQL directo).
CREATE OR REPLACE FUNCTION trg_set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;"""
    )

    # 2) tablas + índices + comentarios (§3.1-§3.22, orden topológico)
    op.execute(
        """CREATE TABLE pe_documento_tipo (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    descripcion   varchar(50) NOT NULL
        CONSTRAINT uq_pe_documento_tipo_descripcion UNIQUE,   -- DNI, LC, LE, Pasaporte
    orden         int,
    activo        boolean NOT NULL DEFAULT true,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz,
    deleted_at    timestamptz
);"""
    )
    op.execute(
        """CREATE TABLE pe_persona (
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_tipo_id  uuid NOT NULL REFERENCES pe_documento_tipo(id)
                                    ON DELETE RESTRICT,
    documento          varchar(20)  NOT NULL,
    apellido           varchar(100) NOT NULL,
    nombre             varchar(100) NOT NULL,
    razon_social       varchar(150),                     -- [CORREGIDO] nullable:
                                                         -- persona física no tiene
    fecha_nacimiento   date,
    sexo               varchar(1),                       -- [CORREGIDO] nullable
    direccion          varchar(150),
    nacionalidad       varchar(50) NOT NULL DEFAULT 'Argentino',
    created_at         timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz,
    deleted_at         timestamptz
);"""
    )
    op.execute(
        """CREATE UNIQUE INDEX uq_persona_documento
    ON pe_persona(documento_tipo_id, documento) WHERE deleted_at IS NULL;"""
    )
    op.execute(
        """CREATE INDEX idx_persona_apellido_nombre ON pe_persona(apellido, nombre);"""
    )
    op.execute(
        """CREATE INDEX idx_persona_activa ON pe_persona(id) WHERE deleted_at IS NULL;"""
    )
    op.execute(
        """CREATE TABLE pe_contacto_tipo (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    descripcion   varchar(50) NOT NULL
        CONSTRAINT uq_pe_contacto_tipo_descripcion UNIQUE,   -- Email, Teléfono, Celular
    activo        boolean NOT NULL DEFAULT true,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz,
    deleted_at    timestamptz
);"""
    )
    op.execute(
        """CREATE TABLE pe_contacto (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    persona_id       uuid NOT NULL REFERENCES pe_persona(id) ON DELETE CASCADE,
    contacto_tipo_id uuid NOT NULL REFERENCES pe_contacto_tipo(id)
                                     ON DELETE RESTRICT,
    descripcion      varchar(150) NOT NULL,       -- valor concreto
    predeterminado   boolean NOT NULL DEFAULT false,
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz,
    deleted_at       timestamptz
);"""
    )
    op.execute(
        """CREATE INDEX idx_contacto_persona ON pe_contacto(persona_id)
    WHERE deleted_at IS NULL;"""
    )
    op.execute(
        """CREATE TABLE us_usuario (
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    persona_id           uuid NOT NULL REFERENCES pe_persona(id)
                                        ON DELETE RESTRICT,
    username             varchar(50)  NOT NULL,
    email                varchar(150),
    password_hash        text         NOT NULL,      -- Argon2id, jamás texto plano
    activo               boolean NOT NULL DEFAULT true,
    bloqueado            boolean NOT NULL DEFAULT false,
    intentos_fallidos    int     NOT NULL DEFAULT 0,
    bloqueado_hasta      timestamptz,
    ultimo_ingreso       timestamptz,
    password_changed_at  timestamptz NOT NULL DEFAULT now(),
    token_version        int     NOT NULL DEFAULT 1, -- claim "ver"
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz,
    deleted_at           timestamptz
);"""
    )
    op.execute(
        """CREATE UNIQUE INDEX uq_usuario_username
    ON us_usuario(username) WHERE deleted_at IS NULL;"""
    )
    op.execute(
        """CREATE UNIQUE INDEX uq_usuario_email
    ON us_usuario(email) WHERE deleted_at IS NULL AND email IS NOT NULL;"""
    )
    op.execute(
        """CREATE INDEX idx_usuario_persona ON us_usuario(persona_id);"""
    )
    op.execute(
        """CREATE TABLE us_rol (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo        varchar(50)  NOT NULL
        CONSTRAINT uq_us_rol_codigo UNIQUE,  -- admin, docente, alumno
    descripcion   varchar(100) NOT NULL,
    activo        boolean NOT NULL DEFAULT true,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz,
    deleted_at    timestamptz
);"""
    )
    op.execute(
        """CREATE TABLE us_permiso (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo        varchar(80) NOT NULL
        CONSTRAINT uq_us_permiso_codigo UNIQUE,   -- mesa.crear, reporte.exportar
    descripcion   varchar(150) NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz,
    deleted_at    timestamptz
);"""
    )
    op.execute(
        """CREATE TABLE us_usuario_rol (
    usuario_id uuid NOT NULL REFERENCES us_usuario(id) ON DELETE CASCADE,
    rol_id     uuid NOT NULL REFERENCES us_rol(id)     ON DELETE CASCADE,
    PRIMARY KEY (usuario_id, rol_id)
);"""
    )
    op.execute(
        """CREATE TABLE us_rol_permiso (
    rol_id     uuid NOT NULL REFERENCES us_rol(id)     ON DELETE CASCADE,
    permiso_id uuid NOT NULL REFERENCES us_permiso(id) ON DELETE CASCADE,
    PRIMARY KEY (rol_id, permiso_id)
);"""
    )
    op.execute(
        """CREATE TABLE us_modulo (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo        varchar(30) NOT NULL
        CONSTRAINT uq_us_modulo_codigo UNIQUE,  -- landing | sigme_web | sigme_mobile
    descripcion   varchar(100) NOT NULL,
    activo        boolean NOT NULL DEFAULT true,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz,
    deleted_at    timestamptz
);"""
    )
    op.execute(
        """CREATE TABLE us_usuario_modulo (
    usuario_id uuid NOT NULL REFERENCES us_usuario(id) ON DELETE CASCADE,
    modulo_id  uuid NOT NULL REFERENCES us_modulo(id)  ON DELETE CASCADE,
    PRIMARY KEY (usuario_id, modulo_id)
);"""
    )
    op.execute(
        """CREATE TABLE us_sesion (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),  -- sid
    usuario_id          uuid NOT NULL REFERENCES us_usuario(id)
                                     ON DELETE CASCADE,
    modulo_id           uuid NOT NULL REFERENCES us_modulo(id)
                                     ON DELETE RESTRICT,
    refresh_token_hash  varchar(64) NOT NULL
        CONSTRAINT uq_us_sesion_refresh_token_hash UNIQUE,  -- SHA-256 hex, NUNCA crudo
    familia_id          uuid NOT NULL,                -- para reuse detection
    estado              varchar(12) NOT NULL DEFAULT 'activo'
                        CHECK (estado IN ('activo','revocado')),
    rotated_at          timestamptz,
    ip                  inet,
    user_agent          varchar(300),
    expires_at          timestamptz NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now()
);"""
    )
    op.execute(
        """CREATE INDEX idx_sesion_usuario ON us_sesion(usuario_id, estado);"""
    )
    op.execute(
        """CREATE INDEX idx_sesion_familia ON us_sesion(familia_id);"""
    )
    op.execute(
        """CREATE INDEX idx_sesion_expira  ON us_sesion(expires_at);"""
    )
    op.execute(
        """CREATE TABLE es_orientacion (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    descripcion   varchar(150) NOT NULL
        CONSTRAINT uq_es_orientacion_descripcion UNIQUE,
      -- Tecnicatura en Gestión y Administración de las Organizaciones
      -- Tecnicatura en Tecnología de los Alimentos
    activo        boolean NOT NULL DEFAULT true,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz,
    deleted_at    timestamptz
);"""
    )
    op.execute(
        """CREATE TABLE es_curso (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    orientacion_id  uuid NOT NULL REFERENCES es_orientacion(id)
                                   ON DELETE RESTRICT,
    descripcion     varchar(100) NOT NULL,   -- "1er Año", "2do Año"...
    anio            int,                     -- 1, 2, 3 (NO hay letra de división)
    activo          boolean NOT NULL DEFAULT true,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz,
    deleted_at      timestamptz
);"""
    )
    op.execute(
        """CREATE INDEX idx_curso_orientacion ON es_curso(orientacion_id);"""
    )
    op.execute(
        """CREATE TABLE es_materia (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    curso_id    uuid NOT NULL REFERENCES es_curso(id) ON DELETE RESTRICT,
    codigo      varchar(20),
    descripcion varchar(150) NOT NULL,
    es_taller   boolean NOT NULL DEFAULT false,   -- [CORREGIDO] marca informativa
    activo      boolean NOT NULL DEFAULT true,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz,
    deleted_at  timestamptz
);"""
    )
    op.execute(
        """CREATE INDEX idx_materia_curso ON es_materia(curso_id);"""
    )
    op.execute(
        """CREATE TABLE es_condicion (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    descripcion     varchar(50) NOT NULL
        CONSTRAINT uq_es_condicion_descripcion UNIQUE,  -- Regular, Previa, Libre
    limite_materias int,          -- NULL = sin límite
    activo          boolean NOT NULL DEFAULT true,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz,
    deleted_at      timestamptz
);"""
    )
    op.execute(
        """CREATE TABLE es_convocatoria (
    id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    descripcion              varchar(100) NOT NULL,  -- "1er Cuatrimestre 2026"
    fecha_inicio_inscripcion date NOT NULL,
    fecha_fin_inscripcion    date NOT NULL,
    -- PD-14 RESUELTO: la columna de fecha común de la v1 (fecha de mesa) se
    -- ELIMINA. La convocatoria no declara fechas de exámenes: cada grupo
    -- declara su propia fecha y su hora (RB-27) y la mesa copia ese par de su
    -- grupo (RB-29).
    activa                   boolean NOT NULL DEFAULT true,
    created_at               timestamptz NOT NULL DEFAULT now(),
    updated_at               timestamptz,
    deleted_at               timestamptz,
    CONSTRAINT ck_convocatoria_ventana  CHECK (fecha_inicio_inscripcion
                                    <= fecha_fin_inscripcion)
);"""
    )
    op.execute(
        """CREATE TABLE es_grupo_horario (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    convocatoria_id uuid NOT NULL REFERENCES es_convocatoria(id)
                               ON DELETE RESTRICT,
    fecha           date NOT NULL,
    hora            time NOT NULL,
    nombre          varchar(100),                -- opcional, informativo:
                                                 -- "Mañana",
                                                 -- "Tarde — talleres"
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz,
    deleted_at      timestamptz
);"""
    )
    op.execute(
        """CREATE INDEX idx_grupo_convocatoria ON es_grupo_horario(convocatoria_id);"""
    )
    op.execute(
        """CREATE INDEX idx_grupo_activa ON es_grupo_horario(id) WHERE deleted_at IS NULL;"""
    )
    op.execute(
        """CREATE UNIQUE INDEX uq_grupo_unico
    ON es_grupo_horario(convocatoria_id, fecha, hora) WHERE deleted_at IS NULL;"""
    )
    op.execute(
        """CREATE TABLE es_mesa_examen (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    convocatoria_id   uuid NOT NULL REFERENCES es_convocatoria(id)
                                     ON DELETE RESTRICT,
    condicion_id      uuid NOT NULL REFERENCES es_condicion(id)
                                     ON DELETE RESTRICT,
    materia_id        uuid NOT NULL REFERENCES es_materia(id)
                                     ON DELETE RESTRICT,
    grupo_id          uuid NOT NULL REFERENCES es_grupo_horario(id)
                                     ON DELETE RESTRICT,   -- ver §3.22
    fecha             date NOT NULL,
    hora              time,
    -- RB-29: fecha y hora son una COPIA SINCRONIZADA del grupo (§3.22): se
    -- actualizan en la MISMA transacción en que se edita el grupo. No son
    -- atributos libres de la mesa.
    estado            varchar(20) NOT NULL DEFAULT 'planificada'
                      CHECK (estado IN ('planificada','cerrada','realizada')),

    -- SNAPSHOT (copia inmutable de la asignación)
    -- Política RB-11: se recalcula SOLO al editar la asignación de la mesa
    -- (cambiar materia/condición). NUNCA cuando se renombra la tabla origen.
    orientacion_nombre varchar(150) NOT NULL,
    curso_nombre       varchar(100) NOT NULL,
    materia_nombre     varchar(150) NOT NULL,
    condicion_nombre   varchar(50)  NOT NULL,

    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz,
    deleted_at        timestamptz
);"""
    )
    op.execute(
        """CREATE UNIQUE INDEX uq_mesa_unica
    ON es_mesa_examen(convocatoria_id, materia_id, condicion_id, fecha)
    WHERE deleted_at IS NULL;"""
    )
    op.execute(
        """CREATE INDEX idx_mesa_fecha      ON es_mesa_examen(fecha);"""
    )
    op.execute(
        """CREATE INDEX idx_mesa_convocatoria ON es_mesa_examen(convocatoria_id);"""
    )
    op.execute(
        """CREATE INDEX idx_mesa_materia    ON es_mesa_examen(materia_id);"""
    )
    op.execute(
        """COMMENT ON COLUMN es_mesa_examen.orientacion_nombre IS
  'Snapshot al crear/editar la mesa. Inmutable ante renombres de es_orientacion.';"""
    )
    op.execute(
        """COMMENT ON COLUMN es_mesa_examen.curso_nombre IS
  'Snapshot al crear/editar la mesa. Inmutable ante renombres de es_curso.';"""
    )
    op.execute(
        """COMMENT ON COLUMN es_mesa_examen.materia_nombre IS
  'Snapshot al crear/editar la mesa. Inmutable ante renombres de es_materia.';"""
    )
    op.execute(
        """COMMENT ON COLUMN es_mesa_examen.condicion_nombre IS
  'Snapshot al crear/editar la mesa. Inmutable ante renombres de es_condicion.';"""
    )
    op.execute(
        """CREATE TABLE es_mesa_inscripcion (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id       uuid NOT NULL REFERENCES us_usuario(id)
                                  ON DELETE RESTRICT,   -- alumno que se inscribe
    mesa_examen_id   uuid NOT NULL REFERENCES es_mesa_examen(id)
                                  ON DELETE RESTRICT,
    convocatoria_id  uuid NOT NULL REFERENCES es_convocatoria(id)
                                  ON DELETE RESTRICT,
    -- COPIA de seguimiento de la mesa (igual que los snapshot de 3.18):
    -- se fija UNA vez al crear la inscripción desde la mesa y NUNCA cambia.
    -- Existe para poder imponer la unicidad por materia a nivel de base de
    -- datos, que es lo que pidió el usuario (RB-08).
    materia_id       uuid NOT NULL REFERENCES es_materia(id)
                                  ON DELETE RESTRICT,
    condicion_id     uuid NOT NULL REFERENCES es_condicion(id)
                                  ON DELETE RESTRICT,   -- condición al anotarse
    -- 'anulado': el propio alumno o el secretario revoca la inscripción por
    -- error de elección (se anotó a la mesa de 1° en vez de la de 2°).
    -- Se conserva la fila para auditoría; no se borra.
    --
    -- NO hay estados de asistencia ni de resultado. El sistema no guarda
    -- quién se presentó ni la nota de la mesa (RB-18, RB-21). Quien tiene
    -- permiso de examen antes de rendir, está inscripto: punto.
    estado           varchar(20) NOT NULL DEFAULT 'inscripto'
                     CHECK (estado IN ('inscripto','anulado')),
    inscripto_en     timestamptz NOT NULL DEFAULT now(),
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz,
    deleted_at       timestamptz
);"""
    )
    op.execute(
        """CREATE UNIQUE INDEX uq_inscripcion_unica
    ON es_mesa_inscripcion(convocatoria_id, usuario_id, materia_id)
    WHERE deleted_at IS NULL AND estado <> 'anulado';"""
    )
    op.execute(
        """CREATE INDEX idx_inscripcion_usuario ON es_mesa_inscripcion(usuario_id);"""
    )
    op.execute(
        """CREATE INDEX idx_inscripcion_mesa    ON es_mesa_inscripcion(mesa_examen_id);"""
    )
    op.execute(
        """CREATE INDEX idx_inscripcion_conv    ON es_mesa_inscripcion(convocatoria_id);"""
    )
    op.execute(
        """CREATE TABLE pr_preinscripcion (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    -- ===== CLIENTE — payload exacto del POST /landing/preinscripcion =====
    nombre_alumno    varchar(150) NOT NULL,   -- nombre completo en un campo
    documento        varchar(20)  NOT NULL,   -- sin tipo: se asume DNI
    fecha_nacimiento date         NOT NULL,
    orientacion      varchar(150) NOT NULL,   -- texto, NO fk (aislamiento)
    nombre_tutor     varchar(150) NOT NULL,    -- O-2: TODOS los campos obligatorios
    email            varchar(150) NOT NULL,

    -- ===== SERVIDOR — no viene en el body =====
    anio_lectivo     int  NOT NULL,           -- de configuración, no enviado
    ip               inet,
    user_agent       varchar(300),
    utm_source       varchar(100),
    utm_medium       varchar(100),
    utm_campaign     varchar(100),
    estado           varchar(20) NOT NULL DEFAULT 'pendiente'
                     CHECK (estado IN ('pendiente','convertido','descartado')),

    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz,
    deleted_at       timestamptz
);"""
    )
    op.execute(
        """CREATE UNIQUE INDEX uq_preinscripcion_unica
    ON pr_preinscripcion(anio_lectivo, documento)
    WHERE deleted_at IS NULL;"""
    )
    op.execute(
        """CREATE INDEX idx_preinscripcion_estado ON pr_preinscripcion(estado);"""
    )
    op.execute(
        """CREATE INDEX idx_preinscripcion_fecha  ON pr_preinscripcion(created_at);"""
    )
    op.execute(
        """CREATE TABLE pr_ventana (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    anio_lectivo  int  NOT NULL,              -- año al que se preinscribe
    descripcion   varchar(100) NOT NULL,      -- "Preinscripción 2027"
    fecha_desde   date NOT NULL,              -- inclusive
    fecha_hasta   date NOT NULL,              -- inclusive
    activa        boolean NOT NULL DEFAULT true,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz,
    deleted_at    timestamptz,
    CONSTRAINT ck_ventana    CHECK (fecha_desde <= fecha_hasta),
    CONSTRAINT uq_ventana_anio UNIQUE (anio_lectivo)
);"""
    )

    # 3) vistas (§3.18, §3.21)
    op.execute(
        """CREATE VIEW vw_mesa_con_alumnos AS
SELECT m.*
FROM es_mesa_examen m
WHERE m.deleted_at IS NULL
  AND EXISTS (
      SELECT 1 FROM es_mesa_inscripcion i
      WHERE i.mesa_examen_id = m.id
        AND i.estado = 'inscripto'
        AND i.deleted_at IS NULL
  );"""
    )
    op.execute(
        """CREATE VIEW vw_ventana_vigente AS
SELECT * FROM pr_ventana
WHERE activa
  AND deleted_at IS NULL
  AND current_date BETWEEN fecha_desde AND fecha_hasta;"""
    )

    # 4) trigger por tabla con updated_at
    op.execute(
        """CREATE TRIGGER set_updated_at BEFORE UPDATE ON pe_documento_tipo
FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();"""
    )
    op.execute(
        """CREATE TRIGGER set_updated_at BEFORE UPDATE ON pe_persona
FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();"""
    )
    op.execute(
        """CREATE TRIGGER set_updated_at BEFORE UPDATE ON pe_contacto_tipo
FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();"""
    )
    op.execute(
        """CREATE TRIGGER set_updated_at BEFORE UPDATE ON pe_contacto
FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();"""
    )
    op.execute(
        """CREATE TRIGGER set_updated_at BEFORE UPDATE ON us_usuario
FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();"""
    )
    op.execute(
        """CREATE TRIGGER set_updated_at BEFORE UPDATE ON us_rol
FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();"""
    )
    op.execute(
        """CREATE TRIGGER set_updated_at BEFORE UPDATE ON us_permiso
FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();"""
    )
    op.execute(
        """CREATE TRIGGER set_updated_at BEFORE UPDATE ON us_modulo
FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();"""
    )
    op.execute(
        """CREATE TRIGGER set_updated_at BEFORE UPDATE ON es_orientacion
FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();"""
    )
    op.execute(
        """CREATE TRIGGER set_updated_at BEFORE UPDATE ON es_curso
FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();"""
    )
    op.execute(
        """CREATE TRIGGER set_updated_at BEFORE UPDATE ON es_materia
FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();"""
    )
    op.execute(
        """CREATE TRIGGER set_updated_at BEFORE UPDATE ON es_condicion
FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();"""
    )
    op.execute(
        """CREATE TRIGGER set_updated_at BEFORE UPDATE ON es_convocatoria
FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();"""
    )
    op.execute(
        """CREATE TRIGGER set_updated_at BEFORE UPDATE ON es_grupo_horario
FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();"""
    )
    op.execute(
        """CREATE TRIGGER set_updated_at BEFORE UPDATE ON es_mesa_examen
FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();"""
    )
    op.execute(
        """CREATE TRIGGER set_updated_at BEFORE UPDATE ON es_mesa_inscripcion
FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();"""
    )
    op.execute(
        """CREATE TRIGGER set_updated_at BEFORE UPDATE ON pr_preinscripcion
FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();"""
    )
    op.execute(
        """CREATE TRIGGER set_updated_at BEFORE UPDATE ON pr_ventana
FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();"""
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS vw_mesa_con_alumnos")
    op.execute("DROP VIEW IF EXISTS vw_ventana_vigente")
    op.execute("DROP TABLE IF EXISTS pr_ventana")
    op.execute("DROP TABLE IF EXISTS pr_preinscripcion")
    op.execute("DROP TABLE IF EXISTS es_mesa_inscripcion")
    op.execute("DROP TABLE IF EXISTS es_mesa_examen")
    op.execute("DROP TABLE IF EXISTS es_grupo_horario")
    op.execute("DROP TABLE IF EXISTS es_convocatoria")
    op.execute("DROP TABLE IF EXISTS es_condicion")
    op.execute("DROP TABLE IF EXISTS es_materia")
    op.execute("DROP TABLE IF EXISTS es_curso")
    op.execute("DROP TABLE IF EXISTS es_orientacion")
    op.execute("DROP TABLE IF EXISTS us_sesion")
    op.execute("DROP TABLE IF EXISTS us_usuario_modulo")
    op.execute("DROP TABLE IF EXISTS us_modulo")
    op.execute("DROP TABLE IF EXISTS us_rol_permiso")
    op.execute("DROP TABLE IF EXISTS us_usuario_rol")
    op.execute("DROP TABLE IF EXISTS us_permiso")
    op.execute("DROP TABLE IF EXISTS us_rol")
    op.execute("DROP TABLE IF EXISTS us_usuario")
    op.execute("DROP TABLE IF EXISTS pe_contacto")
    op.execute("DROP TABLE IF EXISTS pe_contacto_tipo")
    op.execute("DROP TABLE IF EXISTS pe_persona")
    op.execute("DROP TABLE IF EXISTS pe_documento_tipo")
    op.execute("DROP FUNCTION IF EXISTS trg_set_updated_at")
