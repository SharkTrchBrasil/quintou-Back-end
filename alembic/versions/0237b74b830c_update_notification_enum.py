"""update_notification_enum

Revision ID: 0237b74b830c
Revises: c2be76bac7b9
Create Date: 2026-07-14 21:48:14.801481

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0237b74b830c'
down_revision: Union[str, None] = 'c2be76bac7b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Cannot run ALTER TYPE ADD VALUE inside a transaction block in Postgres.
    op.execute("COMMIT")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'BOOKING_COMPLETED'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'BOOKING_REMINDER'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'HOST_REMINDER'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'REVIEW_REQUEST'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'NEW_MESSAGE'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'HOST_WEEKLY_SUMMARY'")

def downgrade() -> None:
    # Downgrading enums in PG is complex, usually we just leave them.
    pass
