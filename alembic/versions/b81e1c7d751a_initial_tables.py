"""Initial tables

Revision ID: b81e1c7d751a
Revises:
Create Date: 2026-02-17 06:44:21.930556

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b81e1c7d751a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Customers
    op.create_table('customers',
        sa.Column('customer_id', sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('tax_id', sa.String(50), nullable=True, unique=True),
        sa.Column('kyc_status', sa.String(20), server_default='PENDING', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )

    # Accounts
    op.create_table('accounts',
        sa.Column('account_id', sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('customer_id', sa.UUID(as_uuid=True), sa.ForeignKey('customers.customer_id'), nullable=False),
        sa.Column('account_type', sa.String(20), nullable=False),
        sa.Column('currency', sa.String(3), server_default='JPY', nullable=False),
        sa.Column('balance', sa.Numeric(19, 4), server_default='0', nullable=False),
        sa.Column('status', sa.String(20), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )

    # Transaction Headers
    op.create_table('transaction_headers',
        sa.Column('transaction_id', sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('idempotency_key', sa.String(255), unique=True, nullable=True),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), server_default='PENDING', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )

    # Transaction Entries (transactions table)
    op.create_table('transactions',
        sa.Column('entry_id', sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('transaction_id', sa.UUID(as_uuid=True), sa.ForeignKey('transaction_headers.transaction_id'), nullable=False),
        sa.Column('account_id', sa.UUID(as_uuid=True), sa.ForeignKey('accounts.account_id'), nullable=False),
        sa.Column('amount', sa.Numeric(19, 4), nullable=False),
        sa.Column('direction', sa.String(10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )

    # Audit Logs
    op.create_table('audit_logs',
        sa.Column('log_id', sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('target_table', sa.String(50), nullable=False),
        sa.Column('target_id', sa.String(50), nullable=False),
        sa.Column('before_data', sa.JSON, nullable=True),
        sa.Column('after_data', sa.JSON, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('transactions')
    op.drop_table('transaction_headers')
    op.drop_table('accounts')
    op.drop_table('customers')
