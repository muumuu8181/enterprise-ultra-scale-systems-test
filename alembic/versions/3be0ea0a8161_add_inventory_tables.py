"""add_inventory_tables

Revision ID: 3be0ea0a8161
Revises: 457bbb7155a1
Create Date: 2026-02-17 07:10:55.300518

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3be0ea0a8161'
down_revision: Union[str, Sequence[str], None] = '457bbb7155a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Items
    op.create_table(
        'items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False, comment='アイテム名'),
        sa.Column('rarity', sa.Integer(), nullable=False, comment='レアリティ'),
        sa.Column('type', sa.String(), nullable=False, comment='アイテムタイプ'),
        sa.Column('stats', sa.JSON(), nullable=True, comment='ステータス (JSON)'),
        sa.Column('description', sa.String(), nullable=True, comment='説明'),
        sa.Column('icon_url', sa.String(), nullable=True, comment='アイコンURL'),
        sa.PrimaryKeyConstraint('id')
    )
    # User Inventories
    op.create_table(
        'user_inventories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='ユーザーID'),
        sa.Column('item_id', sa.Integer(), nullable=False, comment='アイテムID'),
        sa.Column('quantity', sa.Integer(), nullable=False, comment='所持数'),
        sa.Column('acquired_at', sa.DateTime(), nullable=False, comment='取得日時'),
        sa.Column('is_locked', sa.Boolean(), nullable=False, comment='ロック状態'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], )
    )
    # Trade Offers
    op.create_table(
        'trade_offers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('from_user_id', sa.Integer(), nullable=False, comment='申請者ユーザーID'),
        sa.Column('to_user_id', sa.Integer(), nullable=False, comment='対象ユーザーID'),
        sa.Column('offer_items', sa.JSON(), nullable=False, comment='提供アイテム (JSON)'),
        sa.Column('request_items', sa.JSON(), nullable=False, comment='要求アイテム (JSON)'),
        sa.Column('status', sa.String(), nullable=False, server_default='pending', comment='ステータス (pending, accepted, rejected, cancelled)'),
        sa.Column('expires_at', sa.DateTime(), nullable=True, comment='有効期限'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='作成日時'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['from_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['to_user_id'], ['users.id'], )
    )


def downgrade() -> None:
    op.drop_table('trade_offers')
    op.drop_table('user_inventories')
    op.drop_table('items')
