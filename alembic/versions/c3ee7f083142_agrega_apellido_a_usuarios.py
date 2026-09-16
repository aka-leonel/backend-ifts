"""agrega apellido a usuarios

Revision ID: c3ee7f083142
Revises: efcb9afaa1d2
Create Date: 2026-09-15 19:55:16.528428

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3ee7f083142'
down_revision: Union[str, None] = 'efcb9afaa1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default='' rellena las filas existentes para poder agregar la
    # columna como NOT NULL; se retira después para que quede a cargo del
    # modelo/schema de la app (igual que `nombre`), no de la DB. batch_alter_table
    # porque SQLite no soporta ALTER COLUMN ... DROP DEFAULT directamente.
    op.add_column(
        'usuarios',
        sa.Column('apellido', sa.String(), nullable=False, server_default=''),
    )
    with op.batch_alter_table('usuarios') as batch_op:
        batch_op.alter_column('apellido', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('usuarios') as batch_op:
        batch_op.drop_column('apellido')
