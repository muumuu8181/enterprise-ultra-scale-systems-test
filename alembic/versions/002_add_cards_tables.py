"""add_cards_tables

Revision ID: 002
Revises: 001
Create Date: 2024-05-21 10:00:00.000000

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
    # Cards Table
    op.create_table('cards',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('card_number_masked', sa.String(), nullable=False),
        sa.Column('expiry_date', sa.String(length=5), nullable=False),
        sa.Column('cvv_hash', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'FROZEN', 'CANCELLED', name='cardstatus'), nullable=False),
        sa.Column('daily_limit', sa.Float(), nullable=False),
        sa.Column('monthly_limit', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cards_account_id'), 'cards', ['account_id'], unique=False)
    op.create_index(op.f('ix_cards_id'), 'cards', ['id'], unique=False)

    # Card Transactions Table
    op.create_table('card_transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('card_id', sa.Integer(), nullable=False),
        sa.Column('merchant', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'COMPLETED', 'FAILED', 'DECLINED', name='transactionstatus'), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['card_id'], ['cards.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_card_transactions_card_id'), 'card_transactions', ['card_id'], unique=False)
    op.create_index(op.f('ix_card_transactions_id'), 'card_transactions', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_card_transactions_id'), table_name='card_transactions')
    op.drop_index(op.f('ix_card_transactions_card_id'), table_name='card_transactions')
    op.drop_table('card_transactions')
    op.drop_index(op.f('ix_cards_id'), table_name='cards')
    op.drop_index(op.f('ix_cards_account_id'), table_name='cards')
    op.drop_table('cards')
    op.execute("DROP TYPE IF EXISTS cardstatus")
    op.execute("DROP TYPE IF EXISTS transactionstatus")
