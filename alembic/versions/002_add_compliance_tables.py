"""add_compliance_tables

Revision ID: 002
Revises: 001
Create Date: 2024-05-20 12:00:00.000000

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
    # SanctionsCheck Table
    op.create_table(
        'sanctions_checks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='ID'),
        sa.Column('customer_id', sa.String(), nullable=False, comment='顧客ID'),
        sa.Column('status', sa.String(), nullable=False, comment='ステータス (CLEAR, MATCHED, PENDING)'),
        sa.Column('matched_list', sa.String(), nullable=True, comment='一致したリスト名 (OFAC, UNなど)'),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False, comment='照合日時'),
        sa.PrimaryKeyConstraint('id')
    )

    # SAR Table
    op.create_table(
        'sars',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='ID'),
        sa.Column('customer_id', sa.String(), nullable=False, comment='顧客ID'),
        sa.Column('transactions', sa.JSON(), nullable=False, comment='関連取引データ (JSON)'),
        sa.Column('risk_indicators', sa.JSON(), nullable=False, comment='リスク指標リスト (JSON)'),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False, comment='提出日時'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('sars')
    op.drop_table('sanctions_checks')
