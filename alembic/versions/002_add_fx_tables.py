"""add fx tables

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
    # FX Rates Table
    op.create_table('fx_rates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('base_currency', sa.String(length=3), nullable=False),
        sa.Column('quote_currency', sa.String(length=3), nullable=False),
        sa.Column('bid', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('ask', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('mid', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fx_rates_id'), 'fx_rates', ['id'], unique=False)
    # Ideally index on (base, quote, timestamp) for query performance
    op.create_index('ix_fx_rates_pair_timestamp', 'fx_rates', ['base_currency', 'quote_currency', 'timestamp'], unique=False)

    # FX Orders Table
    # Enums are automatically handled by SQLAlchemy for Postgres if using sa.Enum with name.

    op.create_table('fx_orders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('customer_id', sa.String(), nullable=False),
        sa.Column('from_currency', sa.String(length=3), nullable=False),
        sa.Column('to_currency', sa.String(length=3), nullable=False),
        sa.Column('amount', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('order_type', sa.Enum('MARKET', 'LIMIT', name='ordertype'), nullable=False),
        sa.Column('limit_rate', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'FILLED', 'CANCELLED', name='orderstatus'), nullable=False),
        sa.Column('executed_rate', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fx_orders_id'), 'fx_orders', ['id'], unique=False)
    op.create_index(op.f('ix_fx_orders_customer_id'), 'fx_orders', ['customer_id'], unique=False)
    op.create_index('ix_fx_orders_status', 'fx_orders', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_fx_orders_status', table_name='fx_orders')
    op.drop_index(op.f('ix_fx_orders_customer_id'), table_name='fx_orders')
    op.drop_index(op.f('ix_fx_orders_id'), table_name='fx_orders')
    op.drop_table('fx_orders')

    # Drop Enums manually if needed, but SQLAlchemy usually keeps them unless explicitly dropped.
    # Alembic's drop_table doesn't auto-drop types.
    sa.Enum(name='ordertype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='orderstatus').drop(op.get_bind(), checkfirst=True)

    op.drop_index('ix_fx_rates_pair_timestamp', table_name='fx_rates')
    op.drop_index(op.f('ix_fx_rates_id'), table_name='fx_rates')
    op.drop_table('fx_rates')
