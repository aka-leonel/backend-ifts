"""TalentoTech: relacion N:M con carreras + flag todas_las_carreras

Reemplaza `talentotech.carrera_id` por la tabla intermedia
`talentotech_carreras`, agrega `talentotech.todas_las_carreras` y los campos
que necesita la card del front (`institucion`, `modalidad_cursada`,
`dificultad`). La unicidad pasa a (institucion, nombre_curso).

Migracion manual (sin autogenerate). Funciona en SQLite (batch) y PostgreSQL.

Revision ID: e8b3c1d5f7a9
Revises: d4f6a1c9e2b7
Create Date: 2026-11-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e8b3c1d5f7a9"
down_revision: Union[str, None] = "d4f6a1c9e2b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UNIQUE_NUEVA = "uq_talentotech_institucion_curso"
INDICE_CARRERA = "ix_talentotech_carrera_id"


def _es_sqlite() -> bool:
    return op.get_bind().dialect.name == "sqlite"


def _tabla_talentotech_para_batch() -> sa.Table:
    """Esquema origen del batch (incluye carrera_id, que se va a dropear)."""
    return sa.Table(
        "talentotech",
        sa.MetaData(),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("carrera_id", sa.Integer(), nullable=True),
        sa.Column("nombre_curso", sa.String(150), nullable=False),
        sa.Column("categoria", sa.String(20), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("duracion", sa.String(50), nullable=False),
        sa.Column("link_inscripcion", sa.Text(), nullable=False),
        sa.Column("institucion", sa.String(150), nullable=False),
        sa.Column("modalidad_cursada", sa.String(50), nullable=False),
        sa.Column("dificultad", sa.String(30), nullable=True),
        sa.Column(
            "todas_las_carreras",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["carrera_id"], ["carreras.id"]),
        sa.Index("ix_talentotech_id", "id"),
    )


def _tabla_talentotech_downgrade_batch() -> sa.Table:
    """Esquema origen del batch de downgrade (incluye las columnas nuevas)."""
    return sa.Table(
        "talentotech",
        sa.MetaData(),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("carrera_id", sa.Integer(), nullable=True),
        sa.Column("nombre_curso", sa.String(150), nullable=False),
        sa.Column("categoria", sa.String(20), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("duracion", sa.String(50), nullable=False),
        sa.Column("link_inscripcion", sa.Text(), nullable=False),
        sa.Column("institucion", sa.String(150), nullable=False),
        sa.Column("modalidad_cursada", sa.String(50), nullable=False),
        sa.Column("dificultad", sa.String(30), nullable=True),
        sa.Column(
            "todas_las_carreras",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_talentotech_id", "id"),
    )


def _verificar_duplicados(bind) -> None:
    """La nueva unicidad (institucion, nombre_curso) no admite duplicados."""
    duplicados = bind.execute(
        sa.text(
            "SELECT institucion, nombre_curso, COUNT(*) AS total "
            "FROM talentotech "
            "GROUP BY institucion, nombre_curso "
            "HAVING COUNT(*) > 1"
        )
    ).fetchall()
    if duplicados:
        detalle = "; ".join(
            f"institucion={fila[0]!r}, nombre_curso={fila[1]!r} ({fila[2]} filas)"
            for fila in duplicados
        )
        raise RuntimeError(
            "No se puede migrar TalentoTech a N:M: existen duplicados por "
            f"(institucion, nombre_curso): {detalle}. Consolidalos manualmente "
            "antes de correr la migracion."
        )


def upgrade() -> None:
    bind = op.get_bind()

    # 1) Tabla intermedia.
    op.create_table(
        "talentotech_carreras",
        sa.Column("talentotech_id", sa.Integer(), nullable=False),
        sa.Column("carrera_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["talentotech_id"], ["talentotech.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["carrera_id"], ["carreras.id"]),
        sa.PrimaryKeyConstraint("talentotech_id", "carrera_id"),
    )

    # 2) Copiar las carreras existentes antes de dropear la columna.
    bind.execute(
        sa.text(
            "INSERT INTO talentotech_carreras (talentotech_id, carrera_id) "
            "SELECT id, carrera_id FROM talentotech"
        )
    )

    # 3) Columnas nuevas. `institucion` y `modalidad_cursada` no tienen valor
    #    previo: se agregan con default vacio y luego se les quita el default.
    op.add_column(
        "talentotech",
        sa.Column(
            "institucion", sa.String(150), nullable=False, server_default=sa.text("''")
        ),
    )
    op.add_column(
        "talentotech",
        sa.Column(
            "modalidad_cursada",
            sa.String(50),
            nullable=False,
            server_default=sa.text("''"),
        ),
    )
    op.add_column(
        "talentotech", sa.Column("dificultad", sa.String(30), nullable=True)
    )
    op.add_column(
        "talentotech",
        sa.Column(
            "todas_las_carreras",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    _verificar_duplicados(bind)

    if _es_sqlite():
        with op.batch_alter_table(
            "talentotech",
            copy_from=_tabla_talentotech_para_batch(),
            recreate="always",
        ) as batch_op:
            batch_op.create_unique_constraint(
                UNIQUE_NUEVA, ["institucion", "nombre_curso"]
            )
            batch_op.drop_column("carrera_id")
    else:
        indices = {
            indice["name"]
            for indice in sa.inspect(bind).get_indexes("talentotech")
        }
        if INDICE_CARRERA in indices:
            op.drop_index(INDICE_CARRERA, table_name="talentotech")
        op.drop_column("talentotech", "carrera_id")
        op.alter_column("talentotech", "institucion", server_default=None)
        op.alter_column("talentotech", "modalidad_cursada", server_default=None)
        op.create_unique_constraint(
            UNIQUE_NUEVA, "talentotech", ["institucion", "nombre_curso"]
        )


def downgrade() -> None:
    bind = op.get_bind()

    # 1) Recrear la columna (nullable: un curso wildcard no tiene una sola).
    op.add_column(
        "talentotech", sa.Column("carrera_id", sa.Integer(), nullable=True)
    )

    # 2) Reponer una carrera por curso: la primera asociada o la primera
    #    carrera existente.
    bind.execute(
        sa.text(
            "UPDATE talentotech SET carrera_id = ("
            "  SELECT tc.carrera_id FROM talentotech_carreras tc "
            "  WHERE tc.talentotech_id = talentotech.id LIMIT 1"
            ")"
        )
    )
    bind.execute(
        sa.text(
            "UPDATE talentotech SET carrera_id = (SELECT MIN(id) FROM carreras) "
            "WHERE carrera_id IS NULL"
        )
    )

    # 3) Eliminar la tabla intermedia.
    op.drop_table("talentotech_carreras")

    if _es_sqlite():
        with op.batch_alter_table(
            "talentotech",
            copy_from=_tabla_talentotech_downgrade_batch(),
            recreate="always",
        ) as batch_op:
            batch_op.create_index(INDICE_CARRERA, ["carrera_id"])
            batch_op.drop_column("todas_las_carreras")
            batch_op.drop_column("dificultad")
            batch_op.drop_column("modalidad_cursada")
            batch_op.drop_column("institucion")
    else:
        op.drop_constraint(UNIQUE_NUEVA, "talentotech", type_="unique")
        op.create_index(INDICE_CARRERA, "talentotech", ["carrera_id"])
        op.drop_column("talentotech", "todas_las_carreras")
        op.drop_column("talentotech", "dificultad")
        op.drop_column("talentotech", "modalidad_cursada")
        op.drop_column("talentotech", "institucion")
