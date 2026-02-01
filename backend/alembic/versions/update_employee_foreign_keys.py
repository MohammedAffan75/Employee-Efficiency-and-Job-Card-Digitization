"""update employee foreign keys

Revision ID: update_fk_employees
Revises: 
Create Date: 2025-11-08

Updates JobCard and ValidationFlag foreign keys to reference 'employees' table
instead of 'efficiency_employees' table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_update_fk_employees'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old foreign key constraints from job_cards
    op.drop_constraint('job_cards_employee_id_fkey', 'job_cards', type_='foreignkey')
    op.drop_constraint('job_cards_supervisor_id_fkey', 'job_cards', type_='foreignkey')
    
    # Create new foreign key constraints pointing to employees table
    op.create_foreign_key(
        'job_cards_employee_id_fkey', 
        'job_cards', 
        'employees', 
        ['employee_id'], 
        ['id']
    )
    op.create_foreign_key(
        'job_cards_supervisor_id_fkey', 
        'job_cards', 
        'employees', 
        ['supervisor_id'], 
        ['id']
    )
    
    # Drop old foreign key constraint from validation_flags
    op.drop_constraint('validation_flags_resolved_by_fkey', 'validation_flags', type_='foreignkey')
    
    # Create new foreign key constraint pointing to employees table
    op.create_foreign_key(
        'validation_flags_resolved_by_fkey', 
        'validation_flags', 
        'employees', 
        ['resolved_by'], 
        ['id']
    )


def downgrade() -> None:
    # Drop new foreign key constraints from job_cards
    op.drop_constraint('job_cards_employee_id_fkey', 'job_cards', type_='foreignkey')
    op.drop_constraint('job_cards_supervisor_id_fkey', 'job_cards', type_='foreignkey')
    
    # Restore old foreign key constraints pointing to efficiency_employees table
    op.create_foreign_key(
        'job_cards_employee_id_fkey', 
        'job_cards', 
        'efficiency_employees', 
        ['employee_id'], 
        ['id']
    )
    op.create_foreign_key(
        'job_cards_supervisor_id_fkey', 
        'job_cards', 
        'efficiency_employees', 
        ['supervisor_id'], 
        ['id']
    )
    
    # Drop new foreign key constraint from validation_flags
    op.drop_constraint('validation_flags_resolved_by_fkey', 'validation_flags', type_='foreignkey')
    
    # Restore old foreign key constraint pointing to efficiency_employees table
    op.create_foreign_key(
        'validation_flags_resolved_by_fkey', 
        'validation_flags', 
        'efficiency_employees', 
        ['resolved_by'], 
        ['id']
    )
