"""Add UserRole

Revision ID: 23d31f512e23
Revises: edf8b13ea031
Create Date: 2026-07-13 21:53:02.836489

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '23d31f512e23'
down_revision: Union[str, None] = 'edf8b13ea031'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Cria o enum no postgres antes de usar
    userrole = postgresql.ENUM('USER', 'MODERATOR', 'ADMIN', name='userrole')
    userrole.create(op.get_bind(), checkfirst=True)
    
    op.add_column('users', sa.Column('role', sa.Enum('USER', 'MODERATOR', 'ADMIN', name='userrole'), server_default='USER', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'role')
    
    userrole = postgresql.ENUM('USER', 'MODERATOR', 'ADMIN', name='userrole')
    userrole.drop(op.get_bind(), checkfirst=True)
