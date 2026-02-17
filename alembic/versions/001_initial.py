"""initial

Revision ID: 001
Revises:
Create Date: 2024-05-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # PostGIS extension
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')

    # vehicles table
    op.create_table(
        'vehicles',
        sa.Column('id', sa.String(), primary_key=True, comment='車両ID'),
        sa.Column('type', sa.String(), nullable=False, comment='車両タイプ'),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=False, comment='最終確認日時'),
        sa.Column('location', Geography(geometry_type='POINT', srid=4326), nullable=False, comment='現在位置'),
        comment='車両管理テーブル'
    )

    # cam_messages (Cooperative Awareness Message)
    op.create_table(
        'cam_messages',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('vehicle_id', sa.String(), sa.ForeignKey('vehicles.id'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('location', Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('speed', sa.Float(), nullable=False, comment='速度(m/s)'),
        sa.Column('heading', sa.Float(), nullable=False, comment='進行方向(度)'),
        sa.Column('acceleration', sa.Float(), nullable=False, comment='加速度(m/s^2)'),
        comment='CAMメッセージログ'
    )
    # Spatial index for CAM
    op.create_index('idx_cam_location', 'cam_messages', ['location'], postgresql_using='gist')
    op.create_index('idx_cam_timestamp', 'cam_messages', ['timestamp'])

    # denm_messages (Decentralized Environmental Notification Message)
    op.create_table(
        'denm_messages',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('originating_vehicle_id', sa.String(), sa.ForeignKey('vehicles.id'), nullable=True),
        sa.Column('event_type', sa.String(), nullable=False, comment='イベントタイプ'),
        sa.Column('event_position', Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('detection_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('validity_duration', sa.Integer(), nullable=False, comment='有効期間(秒)'),
        comment='DENM危険情報メッセージ'
    )
    # Spatial index for DENM
    op.create_index('idx_denm_position', 'denm_messages', ['event_position'], postgresql_using='gist')

    # spat_messages (Signal Phase and Timing)
    op.create_table(
        'spat_messages',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('intersection_id', sa.String(), nullable=False, comment='交差点ID'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('phase_data', postgresql.JSONB, nullable=False, comment='信号フェーズデータ'),
        comment='SPAT信号情報'
    )
    op.create_index('idx_spat_intersection', 'spat_messages', ['intersection_id'])

    # pki_certificates
    op.create_table(
        'pki_certificates',
        sa.Column('id', sa.String(), primary_key=True, comment='証明書ID'),
        sa.Column('vehicle_id', sa.String(), sa.ForeignKey('vehicles.id'), nullable=False),
        sa.Column('public_key', sa.Text(), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), default=False, comment='失効フラグ'),
        comment='PKI証明書管理'
    )

def downgrade() -> None:
    op.drop_table('pki_certificates')
    op.drop_table('spat_messages')
    op.drop_table('denm_messages')
    op.drop_table('cam_messages')
    op.drop_table('vehicles')
    op.execute('DROP EXTENSION IF EXISTS postgis')
