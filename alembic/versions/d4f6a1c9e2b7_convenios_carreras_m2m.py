"""Convenios: relacion N:M con carreras + flag todas_las_carreras

Reemplaza `convenios.carrera_id` por la tabla intermedia `convenios_carreras`
y agrega `convenios.todas_las_carreras` (D17). La unicidad pasa de
(carrera_id, institucion, carrera_destino) a (institucion, carrera_destino).

Migracion manual (sin autogenerate). Funciona en SQLite (batch) y PostgreSQL.

Revision ID: d4f6a1c9e2b7
Revises: b7d2f8c41a30
Create Date: 2026-10-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4f6a1c9e2b7"
down_revision: Union[str, None] = "b7d2f8c41a30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UNIQUE_VIEJA = "uq_convenios_carrera_institucion_destino"
UNIQUE_NUEVA = "uq_convenios_institucion_destino"
INDICE_CARRERA = "ix_convenios_carrera_id"


def _es_sqlite() -> bool:
    return op.get_bind().dialect.name == "sqlite"


def _tabla_convenios_para_batch(incluir_flag: bool) -> sa.Table:
    """Define explicitamente el esquema origen del batch.

    Evita depender de la reflexion de constraints UNIQUE en SQLite (cuyos
    nombres no siempre se conservan): la tabla resultante se construye solo
    con lo declarado aca mas las operaciones del batch.
    """
    columnas = [
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("carrera_id", sa.Integer(), nullable=True),
        sa.Column("institucion", sa.String(150), nullable=False),
        sa.Column("carrera_destino", sa.String(150), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("link_info", sa.Text(), nullable=False),
    ]
    if incluir_flag:
        columnas.append(
            sa.Column(
                "todas_las_carreras",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        )
    return sa.Table(
        "convenios",
        sa.MetaData(),
        *columnas,
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["carrera_id"], ["carreras.id"]),
        sa.Index("ix_convenios_id", "id"),
    )


def upgrade() -> None:
    bind = op.get_bind()

    # 1) Tabla intermedia.
    op.create_table(
        "convenios_carreras",
        sa.Column("convenio_id", sa.Integer(), nullable=False),
        sa.Column("carrera_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["convenio_id"], ["convenios.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["carrera_id"], ["carreras.id"]),
        sa.PrimaryKeyConstraint("convenio_id", "carrera_id"),
    )

    # 2) Copiar las carreras existentes antes de dropear la columna.
    bind.execute(
        sa.text(
            "INSERT INTO convenios_carreras (convenio_id, carrera_id) "
            "SELECT id, carrera_id FROM convenios"
        )
    )

    # La nueva unicidad es (institucion, carrera_destino): si hubiera filas
    # duplicadas con carreras distintas, la migracion no puede consolidarlas
    # sin perder informacion. Abortamos con un mensaje accionable.
    duplicados = bind.execute(
        sa.text(
            "SELECT institucion, carrera_destino, COUNT(*) AS total "
            "FROM convenios "
            "GROUP BY institucion, carrera_destino "
            "HAVING COUNT(*) > 1"
        )
    ).fetchall()
    if duplicados:
        detalle = "; ".join(
            f"institucion={fila[0]!r}, carrera_destino={fila[1]!r} ({fila[2]} filas)"
            for fila in duplicados
        )
        raise RuntimeError(
            "No se puede migrar convenios a N:M: existen duplicados por "
            f"(institucion, carrera_destino): {detalle}. Consolidalos "
            "manualmente antes de correr la migracion."
        )

    # 3) Flag de wildcard.
    op.add_column(
        "convenios",
        sa.Column(
            "todas_las_carreras",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    if _es_sqlite():
        # Batch con `copy_from`: omite la unique vieja y el indice de
        # carrera_id, y agrega la unique nueva. `drop_column` requiere que
        # carrera_id figure en el esquema origen.
        with op.batch_alter_table(
            "convenios",
            copy_from=_tabla_convenios_para_batch(incluir_flag=True),
            recreate="always",
        ) as batch_op:
            batch_op.create_unique_constraint(
                UNIQUE_NUEVA, ["institucion", "carrera_destino"]
            )
            batch_op.drop_column("carrera_id")
    else:
        op.drop_constraint(UNIQUE_VIEJA, "convenios", type_="unique")
        op.create_unique_constraint(
            UNIQUE_NUEVA, "convenios", ["institucion", "carrera_destino"]
        )
        indices = {
            indice["name"]
            for indice in sa.inspect(bind).get_indexes("convenios")
        }
        if INDICE_CARRERA in indices:
            op.drop_index(INDICE_CARRERA, table_name="convenios")
        op.drop_column("convenios", "carrera_id")


def downgrade() -> None:
    bind = op.get_bind()

    # 1) Recrear la columna (nullable: el esquema viejo la exigia NOT NULL,
    #    pero un convenio wildcard puede no tener filas explicitas).
    op.add_column(
        "convenios", sa.Column("carrera_id", sa.Integer(), nullable=True)
    )

    # 2) Reponer una carrera por convenio: la primera asociada o, si es
    #    wildcard sin filas, la primera carrera existente.
    bind.execute(
        sa.text(
            "UPDATE convenios SET carrera_id = ("
            "  SELECT cc.carrera_id FROM convenios_carreras cc "
            "  WHERE cc.convenio_id = convenios.id LIMIT 1"
            ")"
        )
    )
    bind.execute(
        sa.text(
            "UPDATE convenios SET carrera_id = (SELECT MIN(id) FROM carreras) "
            "WHERE carrera_id IS NULL"
        )
    )

    # 3) Eliminar la tabla intermedia.
    op.drop_table("convenios_carreras")

    if _es_sqlite():
        with op.batch_alter_table(
            "convenios",
            copy_from=_tabla_convenios_para_batch(incluir_flag=True),
            recreate="always",
        ) as batch_op:
            batch_op.create_unique_constraint(
                UNIQUE_VIEJA,
                ["carrera_id", "institucion", "carrera_destino"],
            )
            batch_op.create_index(INDICE_CARRERA, ["carrera_id"])
            batch_op.drop_column("todas_las_carreras")
    else:
        op.drop_constraint(UNIQUE_NUEVA, "convenios", type_="unique")
        op.create_unique_constraint(
            UNIQUE_VIEJA,
            "convenios",
            ["carrera_id", "institucion", "carrera_destino"],
        )
        op.create_index(INDICE_CARRERA, "convenios", ["carrera_id"])
        op.drop_column("convenios", "todas_las_carreras")
