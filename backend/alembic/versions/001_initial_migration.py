"""Initial migration - create all tables

Revision ID: 001
Revises: 
Create Date: 2024-10-28 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables for the Employee Efficiency Tracking System"""
    
    # ==================== Users Table ====================
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('username', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # ==================== Employees Table (Original) ====================
    op.create_table('employees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('first_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('last_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('department', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('position', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('salary', sa.Float(), nullable=False),
        sa.Column('hire_date', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_employees_email'), 'employees', ['email'], unique=True)

    # ==================== Efficiency Employees Table ====================
    op.create_table('efficiency_employees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ec_number', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('role', sa.Enum('OPERATOR', 'SUPERVISOR', 'ADMIN', name='roleenum'), nullable=False),
        sa.Column('team', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('join_date', sa.Date(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_eff_emp_ec_number'), 'efficiency_employees', ['ec_number'], unique=False)
    op.create_index(op.f('ix_efficiency_employees_ec_number'), 'efficiency_employees', ['ec_number'], unique=True)

    # ==================== Machines Table ====================
    op.create_table('machines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('machine_code', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('work_center', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_machines_machine_code'), 'machines', ['machine_code'], unique=True)

    # ==================== Activity Codes Table ====================
    op.create_table('activity_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('std_hours_per_unit', sa.Float(), nullable=True),
        sa.Column('std_qty_per_hour', sa.Float(), nullable=True),
        sa.Column('efficiency_type', sa.Enum('TIME_BASED', 'QUANTITY_BASED', 'TASK_BASED', name='efficiencytypeenum'), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_codes_code'), 'activity_codes', ['code'], unique=True)

    # ==================== Work Orders Table ====================
    op.create_table('work_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('wo_number', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('machine_id', sa.Integer(), nullable=False),
        sa.Column('planned_qty', sa.Float(), nullable=False),
        sa.Column('msd_month', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(['machine_id'], ['machines.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_work_orders_wo_number'), 'work_orders', ['wo_number'], unique=True)

    # ==================== Job Cards Table ====================
    op.create_table('job_cards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=True),
        sa.Column('supervisor_id', sa.Integer(), nullable=True),
        sa.Column('machine_id', sa.Integer(), nullable=False),
        sa.Column('work_order_id', sa.Integer(), nullable=False),
        sa.Column('activity_code_id', sa.Integer(), nullable=True),
        sa.Column('activity_desc', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('qty', sa.Float(), nullable=False),
        sa.Column('actual_hours', sa.Float(), nullable=False),
        sa.Column('status', sa.Enum('IC', 'C', name='jobcardstatusenum'), nullable=False),
        sa.Column('entry_date', sa.Date(), nullable=False),
        sa.Column('source', sa.Enum('TECHNICIAN', 'SUPERVISOR', name='sourceenum'), nullable=False),
        sa.ForeignKeyConstraint(['activity_code_id'], ['activity_codes.id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['efficiency_employees.id'], ),
        sa.ForeignKeyConstraint(['machine_id'], ['machines.id'], ),
        sa.ForeignKeyConstraint(['supervisor_id'], ['efficiency_employees.id'], ),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_orders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobcard_entry_date'), 'job_cards', ['entry_date'], unique=False)
    op.create_index(op.f('ix_jobcard_wo_machine'), 'job_cards', ['work_order_id', 'machine_id'], unique=False)

    # ==================== Validation Flags Table ====================
    op.create_table('validation_flags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_card_id', sa.Integer(), nullable=False),
        sa.Column('flag_type', sa.Enum('DUPLICATION', 'OUTSIDE_MSD', 'AWC', 'SPLIT_CANDIDATE', 'QTY_MISMATCH', name='flagtypeenum'), nullable=False),
        sa.Column('details', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('resolved', sa.Boolean(), nullable=False),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['job_card_id'], ['job_cards.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['efficiency_employees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # ==================== Efficiency Periods Table ====================
    op.create_table('efficiency_periods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('time_efficiency', sa.Float(), nullable=True),
        sa.Column('task_efficiency', sa.Float(), nullable=True),
        sa.Column('quantity_efficiency', sa.Float(), nullable=True),
        sa.Column('awc_pct', sa.Float(), nullable=False),
        sa.Column('standard_hours_allowed', sa.Float(), nullable=False),
        sa.Column('actual_hours', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['efficiency_employees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Drop all tables"""
    op.drop_table('efficiency_periods')
    op.drop_table('validation_flags')
    op.drop_table('job_cards')
    op.drop_table('work_orders')
    op.drop_table('activity_codes')
    op.drop_table('machines')
    op.drop_table('efficiency_employees')
    op.drop_table('employees')
    op.drop_table('users')
