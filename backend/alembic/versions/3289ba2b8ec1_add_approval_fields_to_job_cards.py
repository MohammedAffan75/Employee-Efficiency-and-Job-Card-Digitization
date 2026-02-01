"""add_approval_fields_to_job_cards

Revision ID: 3289ba2b8ec1
Revises: 005_drop_team_column
Create Date: 2025-11-12 23:09:01.854531

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = '3289ba2b8ec1'
down_revision = '005_drop_team_column'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add approval status enum type if it doesn't exist
    op.execute("CREATE TYPE approvalstatusenum AS ENUM ('PENDING', 'APPROVED', 'REJECTED')")
    
    # Add approval-related columns to job_cards table
    op.add_column('job_cards', sa.Column('approval_status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='approvalstatusenum'), nullable=False, server_default='PENDING'))
    op.add_column('job_cards', sa.Column('supervisor_remarks', sa.Text(), nullable=True))
    op.add_column('job_cards', sa.Column('approved_at', sa.DateTime(), nullable=True))
    op.add_column('job_cards', sa.Column('approved_by', sa.Integer(), sa.ForeignKey('employees.id'), nullable=True))


def downgrade() -> None:
    # Remove the columns
    op.drop_column('job_cards', 'approved_by')
    op.drop_column('job_cards', 'approved_at')
    op.drop_column('job_cards', 'supervisor_remarks')
    op.drop_column('job_cards', 'approval_status')
    
    # Drop the enum type
    op.execute("DROP TYPE approvalstatusenum")
