"""Convenios: unicidad (carrera_id, institucion, carrera_destino)

Revision ID: b7d2f8c41a30
Revises: a1c4e7f20b95
Create Date: 2026-10-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d2f8c41a30'
down_revision: Union[str, None] = 'a1c4e7f20b95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CONSTRAINT_NAME = "uq_convenios_carrera_institucion_destino"


def upgrade() -> None:
    """Agrega la unique constraint, abortando si ya hay duplicados.

    `batch_alter_table` es necesario para SQLite (no soporta ALTER TABLE ADD
    CONSTRAINT) y sigue siendo un ALTER normal en PostgreSQL.
    """
    duplicados = op.get_bind().execute(
        sa.text(
            """
            SELECT carrera_id, institucion, carrera_destino, COUNT(*) AS total
            FROM convenios
            GROUP BY carrera_id, institucion, carrera_destino
            HAVING COUNT(*) > 1
            """
        )
    ).fetchall()

    if duplicados:
        detalle = "; ".join(
            f"carrera_id={fila[0]!r}, institucion={fila[1]!r}, "
            f"carrera_destino={fila[2]!r} ({fila[3]} filas)"
            for fila in duplicados
        )
        raise RuntimeError(
            "No se puede crear la unique constraint de convenios: existen "
            f"duplicados por (carrera_id, institucion, carrera_destino): {detalle}"
        )

    with op.batch_alter_table("convenios") as batch_op:
        batch_op.create_unique_constraint(
            CONSTRAINT_NAME,
            ["carrera_id", "institucion", "carrera_destino"],
        )


def downgrade() -> None:
    """Elimina la unique constraint."""
    with op.batch_alter_table("convenios") as batch_op:
        batch_op.drop_constraint(CONSTRAINT_NAME, type_="unique")
