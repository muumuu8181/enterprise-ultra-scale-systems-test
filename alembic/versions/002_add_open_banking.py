"""add open banking tables

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
    # Consents Table
    op.create_table('consents',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('customer_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('scopes', sa.JSON(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'AUTHORIZED', 'REVOKED', 'EXPIRED', name='consentstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Consent Audit Logs Table
    op.create_table('consent_audit_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('consent_id', sa.Uuid(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['consent_id'], ['consents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('consent_audit_logs')
    op.drop_table('consents')
    # Drop enum type if needed, but usually OK to leave or explicit drop
    sa.Enum(name='consentstatus').drop(op.get_bind(), checkfirst=True)
