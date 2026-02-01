"""drop team column from employees table

Revision ID: 005_drop_team_column
Revises: 004_update_remaining_fkeys
Create Date: 2025-11-11

Removes the team column from employees table as teams are no longer used.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_drop_team_column'
down_revision: Union[str, None] = '004_update_remaining_fkeys'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the team column from employees table
    op.drop_column('employees', 'team')


def downgrade() -> None:
    # Add back the team column (nullable string)
    op.add_column('employees', sa.Column('team', sa.String(), nullable=True))
