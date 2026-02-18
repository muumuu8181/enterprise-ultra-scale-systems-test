"""add_kyc

Revision ID: 002
Revises: 001
Create Date: 2024-05-20 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # KYC Applications Table
    op.create_table('kyc_applications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('customer_id', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'VERIFIED', 'REJECTED', name='kycstatus'), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.String(), nullable=True),
        sa.Column('documents', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kyc_applications_customer_id'), 'kyc_applications', ['customer_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_kyc_applications_customer_id'), table_name='kyc_applications')
    op.drop_table('kyc_applications')
    # Clean up Enum type
    sa.Enum(name='kycstatus').drop(op.get_bind(), checkfirst=True)
