"""add is_awc to job_cards

Revision ID: 61f813de380d
Revises: 5c5c9757c280
Create Date: 2025-11-13 19:29:37.346307

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = '61f813de380d'
down_revision = '5c5c9757c280'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add column nullable with a temporary default so existing rows pass
    op.add_column(
        'job_cards',
        sa.Column('is_awc', sa.Boolean(), nullable=True, server_default=sa.text('false'))
    )

    # Backfill existing rows explicitly (defensive)
    op.execute("UPDATE job_cards SET is_awc = false WHERE is_awc IS NULL")

    # Now enforce NOT NULL and drop the default
    op.alter_column(
        'job_cards',
        'is_awc',
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=None,
    )


def downgrade() -> None:
    # Drop the column
    op.drop_column('job_cards', 'is_awc')
