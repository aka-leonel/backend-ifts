"""Add push subscription model

Revision ID: ca3b7b9ab353
Revises: e763065820f1
Create Date: 2026-09-26 00:43:35.041420

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca3b7b9ab353'
down_revision: Union[str, None] = 'e763065820f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('push_subscriptions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('endpoint', sa.String(), nullable=False),
    sa.Column('p256dh', sa.String(), nullable=False),
    sa.Column('auth', sa.String(), nullable=False),
    sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('usuario_id', 'endpoint', name='uq_push_subscription_usuario_endpoint')
    )
    op.create_index(op.f('ix_push_subscriptions_endpoint'), 'push_subscriptions', ['endpoint'], unique=True)
    op.create_index(op.f('ix_push_subscriptions_id'), 'push_subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_push_subscriptions_usuario_id'), 'push_subscriptions', ['usuario_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_push_subscriptions_usuario_id'), table_name='push_subscriptions')
    op.drop_index(op.f('ix_push_subscriptions_id'), table_name='push_subscriptions')
    op.drop_index(op.f('ix_push_subscriptions_endpoint'), table_name='push_subscriptions')
    op.drop_table('push_subscriptions')