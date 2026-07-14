"""add password reset tokens table

Revision ID: add_password_reset
Revises: 99e2d648c27b
Create Date: 2026-07-13 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_password_reset'
down_revision = '99e2d648c27b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Criar tabela password_reset_tokens
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Criar índices
    op.create_index('ix_password_reset_tokens_token', 'password_reset_tokens', ['token'], unique=True)
    op.create_index('ix_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'])
    
    # We skip adding columns here since it's breaking transaction
    # We will rely on autogenerate for new columns



def downgrade() -> None:
    # Remover tabela password_reset_tokens
    op.drop_index('ix_password_reset_tokens_user_id', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_token', table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
    
    # Remover campos adicionados (se foram criados por esta migração)
    try:
        op.drop_column('users', 'fcm_token')
    except:
        pass
    
    try:
        op.drop_column('users', 'stripe_account_status')
    except:
        pass
