"""initial

Revision ID: 001
Revises:
Create Date: 2024-05-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('username', sa.String(length=50), nullable=False, unique=True),
        sa.Column('email', sa.String(length=100), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Gacha Banners
    op.create_table('gacha_banners',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
    )

    # Gacha Rates (Assuming items are managed elsewhere or simple IDs here)
    op.create_table('gacha_rates',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('banner_id', sa.Integer(), sa.ForeignKey('gacha_banners.id'), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('rate', sa.Numeric(precision=5, scale=4), nullable=False), # e.g. 0.0050
    )

    # Gacha Logs
    op.create_table('gacha_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('banner_id', sa.Integer(), sa.ForeignKey('gacha_banners.id'), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # User Pity Counters
    op.create_table('user_pity_counters',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('banner_id', sa.Integer(), sa.ForeignKey('gacha_banners.id'), nullable=False),
        sa.Column('counter', sa.Integer(), default=0, nullable=False),
        sa.UniqueConstraint('user_id', 'banner_id', name='uq_user_banner_pity'),
    )

    # Live Events
    op.create_table('live_events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
    )

    # Event Points
    op.create_table('event_points',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('live_events.id'), nullable=False),
        sa.Column('points', sa.Integer(), default=0, nullable=False),
        sa.UniqueConstraint('user_id', 'event_id', name='uq_user_event_points'),
    )

    # Shop Items
    op.create_table('shop_items',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False), # Assuming currency amount
        sa.Column('currency_type', sa.String(length=20), default='gem', nullable=False),
    )

    # Purchases
    op.create_table('purchases',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('shop_item_id', sa.Integer(), sa.ForeignKey('shop_items.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('purchases')
    op.drop_table('shop_items')
    op.drop_table('event_points')
    op.drop_table('live_events')
    op.drop_table('user_pity_counters')
    op.drop_table('gacha_logs')
    op.drop_table('gacha_rates')
    op.drop_table('gacha_banners')
    op.drop_table('users')
