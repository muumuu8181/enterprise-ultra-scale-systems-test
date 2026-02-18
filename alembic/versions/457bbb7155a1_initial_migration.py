"""initial_migration

Revision ID: 457bbb7155a1
Revises:
Create Date: 2024-05-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '457bbb7155a1'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('currency', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Gacha
    op.create_table(
        'gacha_banners',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('pool_type', sa.String(length=50), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('display_priority', sa.Integer(), default=0),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'gacha_rates',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('banner_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.String(length=50), nullable=False),
        sa.Column('rarity', sa.Integer(), nullable=False),
        sa.Column('weight', sa.Integer(), nullable=False),
        sa.Column('is_pickup', sa.Boolean(), default=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['banner_id'], ['gacha_banners.id'], )
    )

    # User Pity
    op.create_table(
        'user_pity_counters',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('pool_type', sa.String(length=50), nullable=False),
        sa.Column('pity_count', sa.Integer(), default=0),
        sa.Column('hard_pity_count', sa.Integer(), default=0),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now()),
        sa.PrimaryKeyConstraint('user_id', 'pool_type'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )

    # Events
    op.create_table(
        'live_events',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'event_points',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('point', sa.BigInteger(), default=0),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now()),
        sa.PrimaryKeyConstraint('user_id', 'event_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['event_id'], ['live_events.id'], )
    )

    # Partitioned Tables
    op.create_table(
        'gacha_logs',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('banner_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.String(length=50), nullable=False),
        sa.Column('rarity', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id', 'created_at'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['banner_id'], ['gacha_banners.id'], ),
        postgresql_partition_by='RANGE (created_at)'
    )
    # Create a default partition for logs
    op.execute(
        "CREATE TABLE gacha_logs_default PARTITION OF gacha_logs DEFAULT"
    )

    op.create_table(
        'purchases',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('currency_added', sa.Integer(), nullable=False),
        sa.Column('receipt_id', sa.String(length=100), nullable=False),
        sa.Column('verified', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id', 'created_at'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.UniqueConstraint('receipt_id', 'created_at', name='uq_purchases_receipt_id_created_at'),
        postgresql_partition_by='RANGE (created_at)'
    )
    op.execute(
        "CREATE TABLE purchases_default PARTITION OF purchases DEFAULT"
    )


def downgrade() -> None:
    # Drop partitions usually dropped with parent table
    op.drop_table('purchases')
    op.drop_table('gacha_logs')
    op.drop_table('event_points')
    op.drop_table('live_events')
    op.drop_table('user_pity_counters')
    op.drop_table('gacha_rates')
    op.drop_table('gacha_banners')
    op.drop_table('users')
