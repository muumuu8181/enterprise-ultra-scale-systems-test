"""add openbanking tables

Revision ID: 003
Revises: 002
Create Date: 2024-05-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Bank Connections
    op.create_table('bank_connections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('bank_name', sa.String(), nullable=False),
        sa.Column('access_token', sa.String(), nullable=False),
        sa.Column('refresh_token', sa.String(), nullable=True),
        sa.Column('scope', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'EXPIRED', 'REVOKED', name='connectionstatus'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bank_connections_id'), 'bank_connections', ['id'], unique=False)
    op.create_index(op.f('ix_bank_connections_user_id'), 'bank_connections', ['user_id'], unique=False)

    # Bank Accounts
    op.create_table('bank_accounts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('account_number_hash', sa.String(), nullable=False),
        sa.Column('account_type', sa.Enum('CHECKING', 'SAVINGS', 'CREDIT', name='accounttype'), nullable=False),
        sa.Column('balance', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('last_synced', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['connection_id'], ['bank_connections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bank_accounts_id'), 'bank_accounts', ['id'], unique=False)

    # Transactions
    op.create_table('bank_transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('merchant', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('enriched_category', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['bank_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bank_transactions_id'), 'bank_transactions', ['id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_bank_transactions_id'), table_name='bank_transactions')
    op.drop_table('bank_transactions')

    op.drop_index(op.f('ix_bank_accounts_id'), table_name='bank_accounts')
    op.drop_table('bank_accounts')
    sa.Enum(name='accounttype').drop(op.get_bind(), checkfirst=True)

    op.drop_index(op.f('ix_bank_connections_user_id'), table_name='bank_connections')
    op.drop_index(op.f('ix_bank_connections_id'), table_name='bank_connections')
    op.drop_table('bank_connections')
    sa.Enum(name='connectionstatus').drop(op.get_bind(), checkfirst=True)
