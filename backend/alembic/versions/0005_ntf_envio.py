"""0005: cola de email obligatoria ntf_envio (RB-25 / NFR-033)

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-12

RB-25 [obligatoria desde v1]: todo envío queda registrado en `ntf_envio` con
`estado` y `reintentos` (NFR-033); el fallo del proveedor ocurre DESPUÉS de la
respuesta HTTP y no modifica ninguna fila de negocio (NFR-034 / EX-21). El
contrato de reintento programado sigue ABIERTO (PD-04 lo dejó explícito):
esta tabla sólo materializa el estado de cada envío; el reintento lo dará el
worker cuando se cierre ese contrato.

Razón social del cambio: hasta ahora no existía infraestructura de email y el
restablecimiento de clave (decisión 2026-11-04) no enviaba correo. El flujo
automático con verificación por correo (decisión 2026-11-12) necesita registrar
el envío del token.
"""
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """CREATE TABLE ntf_envio (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at    timestamptz NOT NULL DEFAULT now(),
    destinatario  varchar(320) NOT NULL,
    asunto        varchar(200) NOT NULL,
    cuerpo        text NOT NULL,
    estado        varchar(20) NOT NULL DEFAULT 'pendiente'
        CONSTRAINT ck_ntf_envio_estado
        CHECK (estado IN ('pendiente','enviado','fallido')),
    reintentos    integer NOT NULL DEFAULT 0,
    ultimo_error  varchar(500)
);"""
    )
    op.execute(
        """CREATE INDEX idx_ntf_envio_estado
    ON ntf_envio(estado, created_at);"""
    )
    op.execute(
        """COMMENT ON TABLE ntf_envio IS
    'RB-25 (NFR-033): cola de email obligatoria desde v1; estado y reintentos
    de cada envio. El fallo del proveedor es posterior a la respuesta HTTP
    (NFR-034 / EX-21) y nunca modifica filas de negocio.';"""
    )
    op.execute(
        """COMMENT ON COLUMN ntf_envio.estado IS
    'pendiente = encolado sin entregar; enviado = proveedor acepto;
    fallido = ultimo intento rechazado (reintentos cuenta los fallos).';"""
    )
    op.execute(
        """COMMENT ON COLUMN ntf_envio.cuerpo IS
    'Cuerpo del email en claro hasta que se entregue: aqui viaja el token de
    recuperacion (RB-25), NUNCA en us_password_reset.';"""
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ntf_envio")
