"""add_mes_tables

Revision ID: 003
Revises: 002
Create Date: 2024-05-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # WorkOrder Table
    op.create_table(
        'work_orders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.String(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('scheduled_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actual_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('defect_count', sa.Integer(), nullable=False, default=0),
        sa.PrimaryKeyConstraint('id')
    )

    # ProductionLine Table
    op.create_table(
        'production_lines',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('capacity_per_hour', sa.Integer(), nullable=False),
        sa.Column('current_status', sa.String(), nullable=False),
        sa.Column('oee_score', sa.Float(), nullable=False, default=0.0),
        sa.PrimaryKeyConstraint('id')
    )

    # QualityCheck Table
    op.create_table(
        'quality_checks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('work_order_id', sa.Integer(), nullable=False),
        sa.Column('checkpoint_name', sa.String(), nullable=False),
        sa.Column('result', sa.String(), nullable=False),
        sa.Column('measured_value', sa.Float(), nullable=False),
        sa.Column('spec_min', sa.Float(), nullable=False),
        sa.Column('spec_max', sa.Float(), nullable=False),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_orders.id'], )
    )


def downgrade() -> None:
    op.drop_table('quality_checks')
    op.drop_table('production_lines')
    op.drop_table('work_orders')
