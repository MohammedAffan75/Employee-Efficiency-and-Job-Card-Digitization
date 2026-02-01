"""update remaining efficiency_employees foreign keys

Revision ID: 004_update_remaining_fkeys
Revises: 003_update_fk_employees
Create Date: 2025-11-08

Updates AuditLog and EfficiencyPeriod foreign keys to reference 'employees' table
instead of 'efficiency_employees' table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_update_remaining_fkeys'
down_revision: Union[str, None] = '003_update_fk_employees'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop and recreate audit_logs foreign key
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'audit_logs_performed_by_fkey'
            ) THEN
                ALTER TABLE audit_logs DROP CONSTRAINT audit_logs_performed_by_fkey;
            END IF;
        END $$;
    """)
    
    op.create_foreign_key(
        'audit_logs_performed_by_fkey', 
        'audit_logs', 
        'employees', 
        ['performed_by'], 
        ['id']
    )
    
    # Drop and recreate efficiency_periods foreign key
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'efficiency_periods_employee_id_fkey'
            ) THEN
                ALTER TABLE efficiency_periods DROP CONSTRAINT efficiency_periods_employee_id_fkey;
            END IF;
        END $$;
    """)
    
    op.create_foreign_key(
        'efficiency_periods_employee_id_fkey', 
        'efficiency_periods', 
        'employees', 
        ['employee_id'], 
        ['id']
    )


def downgrade() -> None:
    # Drop new foreign key constraint from audit_logs
    op.drop_constraint('audit_logs_performed_by_fkey', 'audit_logs', type_='foreignkey')
    
    # Restore old foreign key constraint pointing to efficiency_employees table
    op.create_foreign_key(
        'audit_logs_performed_by_fkey', 
        'audit_logs', 
        'efficiency_employees', 
        ['performed_by'], 
        ['id']
    )
    
    # Drop new foreign key constraint from efficiency_periods
    op.drop_constraint('efficiency_periods_employee_id_fkey', 'efficiency_periods', type_='foreignkey')
    
    # Restore old foreign key constraint pointing to efficiency_employees table
    op.create_foreign_key(
        'efficiency_periods_employee_id_fkey', 
        'efficiency_periods', 
        'efficiency_employees', 
        ['employee_id'], 
        ['id']
    )
