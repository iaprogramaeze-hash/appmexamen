"""0004: tabla es_dispositivo para push notifications (SDD-4 T6, S6)

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-31

Tabla `es_dispositivo`: un usuario puede registrar varios dispositivos.
Upsert por (usuario_id, device_id) con índice único parcial (deleted_at IS NULL).
Incluye enum `plataforma_dispositivo` (ios, android, web).
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enum plataforma_dispositivo
    plataforma_enum = sa.Enum("ios", "android", "web",
                              name="plataforma_dispositivo", create_constraint=True)
    plataforma_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "es_dispositivo",
        sa.Column("id", sa.Uuid(), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.String(255), nullable=False),
        # create_type=False: el tipo ya lo creó el create() de arriba con
        # checkfirst; sin esto CREATE TABLE vuelve a emitir CREATE TYPE y
        # Postgres responde "type already exists" (bug reproducido 2026-11-04).
        sa.Column("plataforma", postgresql.ENUM(
            "ios", "android", "web", name="plataforma_dispositivo",
            create_constraint=True, create_type=False), nullable=False),
        sa.Column("push_token", sa.String(512), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False,
                  server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["us_usuario.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Índice único parcial: un device_id por usuario (vivo)
    op.create_index(
        "uq_dispositivo_usuario_device",
        "es_dispositivo",
        ["usuario_id", "device_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    # Índice para consultas por usuario
    op.create_index(
        "ix_dispositivo_usuario_id",
        "es_dispositivo",
        ["usuario_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_dispositivo_usuario_id", table_name="es_dispositivo")
    op.drop_index("uq_dispositivo_usuario_device", table_name="es_dispositivo")
    op.drop_table("es_dispositivo")
    sa.Enum(name="plataforma_dispositivo").drop(op.get_bind(), checkfirst=True)