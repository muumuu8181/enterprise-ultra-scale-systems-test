"""fleet tables

Revision ID: 002
Revises: 001
Create Date: 2024-05-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # fleets table
    op.create_table(
        'fleets',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False, comment='フリート名'),
        sa.Column('owner_id', sa.String(), nullable=False, comment='所有者ID'),
        sa.Column('vehicle_count', sa.Integer(), default=0, comment='所属車両数'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='作成日時'),
        comment='フリート情報を管理するテーブル'
    )

    # fleet_vehicles table
    op.create_table(
        'fleet_vehicles',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('fleet_id', sa.Integer(), sa.ForeignKey('fleets.id', ondelete='CASCADE'), nullable=False, comment='所属フリートID'),
        sa.Column('vehicle_id', sa.String(), sa.ForeignKey('vehicles.id'), nullable=False, comment='車両ID'),
        sa.Column('model', sa.String(), comment='車両モデル'),
        sa.Column('status', sa.String(), default='active', comment='ステータス'),
        sa.Column('current_driver_id', sa.String(), nullable=True, comment='現在のドライバーID'),
        sa.Column('odometer', sa.Float(), default=0.0, comment='総走行距離(km)'),
        comment='フリートに所属する車両のテーブル'
    )

    # fleet_tasks table
    op.create_table(
        'fleet_tasks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('fleet_id', sa.Integer(), sa.ForeignKey('fleets.id', ondelete='CASCADE'), nullable=False, comment='関連フリートID'),
        sa.Column('vehicle_id', sa.Integer(), sa.ForeignKey('fleet_vehicles.id'), nullable=True, comment='割り当て車両ID'),
        sa.Column('task_type', sa.String(), nullable=False, comment='タスクタイプ'),
        sa.Column('destination', Geography(geometry_type='POINT', srid=4326), nullable=False, comment='目的地座標'),
        sa.Column('priority', sa.Integer(), default=0, comment='優先度'),
        sa.Column('status', sa.String(), default='pending', comment='タスクステータス'),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True, comment='割り当て日時'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='作成日時'),
        comment='フリート車両への割り当てタスクを管理するテーブル'
    )

def downgrade() -> None:
    op.drop_table('fleet_tasks')
    op.drop_table('fleet_vehicles')
    op.drop_table('fleets')
