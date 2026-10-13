"""Agrega quiz_usos

Revision ID: a1c4e7f20b95
Revises: ca3b7b9ab353
Create Date: 2026-10-13 20:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a1c4e7f20b95'
down_revision: Union[str, None] = 'ca3b7b9ab353'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('quiz_usos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('fecha', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quiz_usos_id'), 'quiz_usos', ['id'], unique=False)
    op.create_index(op.f('ix_quiz_usos_usuario_id'), 'quiz_usos', ['usuario_id'], unique=False)
    op.create_index(op.f('ix_quiz_usos_fecha'), 'quiz_usos', ['fecha'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_quiz_usos_fecha'), table_name='quiz_usos')
    op.drop_index(op.f('ix_quiz_usos_usuario_id'), table_name='quiz_usos')
    op.drop_index(op.f('ix_quiz_usos_id'), table_name='quiz_usos')
    op.drop_table('quiz_usos')
