"""add hashed_password to efficiency_employees

Revision ID: 002
Revises: 001
Create Date: 2024-10-28 23:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add hashed_password column to efficiency_employees table."""
    op.add_column('efficiency_employees', 
        sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='')
    )
    # Note: After running this, use seed_users.py to set proper passwords


def downgrade() -> None:
    """Remove hashed_password column."""
    op.drop_column('efficiency_employees', 'hashed_password')
