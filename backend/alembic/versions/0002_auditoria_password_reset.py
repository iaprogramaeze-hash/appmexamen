"""0002: tablas planeadas us_password_reset (PD-04) y aud_evento (PD-05)

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-20

PD-04 [CERRADO 2026-10-06]: reset de clave por email desde v1, con la tabla
adicional `us_password_reset`; el email lo envía la cola obligatoria (RB-25).
PD-05 [CERRADO 2026-10-06]: bitácora `aud_evento` append-only con snapshot
JSONB; el snapshot no puede contener password_hash, refresh tokens ni hashes
de sesión. Ambas tablas son las únicas que faltaban del diseño cerrado.
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) PD-04 — tokens de restablecimiento de clave (sólo hash SHA-256)
    op.execute(
        """CREATE TABLE us_password_reset (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id    uuid NOT NULL REFERENCES us_usuario(id)
                               ON DELETE CASCADE,
    token_hash    varchar(64) NOT NULL
        CONSTRAINT uq_us_password_reset_token_hash UNIQUE,  -- SHA-256 hex, NUNCA crudo
    ip            inet,
    user_agent    varchar(300),
    expira_en     timestamptz NOT NULL,
    usado_en      timestamptz,       -- Uso único: marcado al restablecer
    created_at    timestamptz NOT NULL DEFAULT now()
);"""
    )
    op.execute(
        """CREATE INDEX idx_us_password_reset_usuario_id
    ON us_password_reset(usuario_id);"""
    )
    op.execute(
        """COMMENT ON TABLE us_password_reset IS """
        "'PD-04 (CERRADO 2026-10-06): tokens opacos de restablecimiento "
        "de clave; se persiste solo su hash SHA-256.';"
    )
    op.execute(
        """COMMENT ON COLUMN us_password_reset.token_hash IS
    'SHA-256 hex del token opaco; el token en claro viaja solo por la cola de email (RB-25).';"""
    )
    op.execute(
        """COMMENT ON COLUMN us_password_reset.usado_en IS
    'Uso unico: se marca al restablecer la clave; NULL = pendiente valido.';"""
    )

    # 2) PD-05 — bitácora append-only con snapshot JSONB
    op.execute(
        """CREATE TABLE aud_evento (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at    timestamptz NOT NULL DEFAULT now(),
    usuario_id    uuid REFERENCES us_usuario(id) ON DELETE RESTRICT,
    username      varchar(50),       -- denormalizado: sobrevive al borrado logico
    modulo        varchar(30),       -- denormalizado: sigme_web | sigme_mobile | landing
    accion        varchar(60) NOT NULL,  -- kebab-case, convencion PD-24
    entidad       varchar(100) NOT NULL, -- tabla o recurso afectado
    entidad_id    varchar(36),
    resultado     varchar(20) NOT NULL
        CONSTRAINT ck_aud_evento_resultado CHECK (resultado IN ('ok','denegado')),
    ip            inet,
    user_agent    varchar(300),
    snapshot      jsonb              -- SIN password_hash/tokens/hashes de sesion (PD-05)
);"""
    )
    op.execute(
        """CREATE INDEX idx_aud_evento_created_at ON aud_evento(created_at);"""
    )
    op.execute(
        """CREATE INDEX idx_aud_evento_usuario_id ON aud_evento(usuario_id);"""
    )
    op.execute("""CREATE INDEX idx_aud_evento_accion ON aud_evento(accion);""")
    op.execute(
        """CREATE INDEX idx_aud_evento_entidad ON aud_evento(entidad, entidad_id);"""
    )
    op.execute(
        """COMMENT ON TABLE aud_evento IS """
        "'PD-05 (CERRADO 2026-10-06): bitacora append-only de escrituras "
        "exitosas, intentos denegados (401/403) y descargas/impresiones de "
        "reportes; las lecturas corrientes se EXCLUYEN.';"
    )
    op.execute(
        """COMMENT ON COLUMN aud_evento.snapshot IS """
        "'JSONB con antes/despues o payload relevante; PROHIBIDO "
        "password_hash, refresh tokens y hashes de sesion (PD-05).';"
    )
    # 3) Append-only real: UPDATE/DELETE revientan en Postgres (PD-05).
    op.execute(
        """CREATE OR REPLACE FUNCTION trg_aud_evento_bloquear() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'aud_evento es append-only (PD-05): % no permitido', TG_OP;
END;
$$ LANGUAGE plpgsql;"""
    )
    op.execute(
        """CREATE TRIGGER trg_aud_evento_append_only
    BEFORE UPDATE OR DELETE ON aud_evento
    FOR EACH ROW EXECUTE FUNCTION trg_aud_evento_bloquear();"""
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_aud_evento_append_only ON aud_evento")
    op.execute("DROP FUNCTION IF EXISTS trg_aud_evento_bloquear")
    op.execute("DROP TABLE IF EXISTS aud_evento")
    op.execute("DROP TABLE IF EXISTS us_password_reset")
