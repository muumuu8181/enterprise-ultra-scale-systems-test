"""mission_ops_tables

Revision ID: 003
Revises: 002
Create Date: 2025-02-17 12:00:00.000000

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
    # Satellites
    op.create_table('satellites',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('tle_line1', sa.String(), nullable=True),
        sa.Column('tle_line2', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('health_metrics', sa.JSON(), nullable=True),
        sa.Column('orbit_params', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_satellites_id'), 'satellites', ['id'], unique=False)
    op.create_index(op.f('ix_satellites_name'), 'satellites', ['name'], unique=True)

    # Ground Stations
    op.create_table('ground_stations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('elevation', sa.Float(), nullable=True),
        sa.Column('min_elevation_angle', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_ground_stations_id'), 'ground_stations', ['id'], unique=False)

    # Telemetry
    op.create_table('telemetry',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('satellite_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['satellite_id'], ['satellites.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_telemetry_id'), 'telemetry', ['id'], unique=False)

    # Anomaly Logs
    op.create_table('anomaly_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('satellite_id', sa.Integer(), nullable=True),
        sa.Column('severity', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('recommended_action', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['satellite_id'], ['satellites.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_anomaly_logs_id'), 'anomaly_logs', ['id'], unique=False)

    # Alert Configurations
    op.create_table('alert_configurations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('satellite_id', sa.Integer(), nullable=True),
        sa.Column('thresholds', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['satellite_id'], ['satellites.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alert_configurations_id'), 'alert_configurations', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_alert_configurations_id'), table_name='alert_configurations')
    op.drop_table('alert_configurations')
    op.drop_index(op.f('ix_anomaly_logs_id'), table_name='anomaly_logs')
    op.drop_table('anomaly_logs')
    op.drop_index(op.f('ix_telemetry_id'), table_name='telemetry')
    op.drop_table('telemetry')
    op.drop_index(op.f('ix_ground_stations_id'), table_name='ground_stations')
    op.drop_table('ground_stations')
    op.drop_index(op.f('ix_satellites_name'), table_name='satellites')
    op.drop_index(op.f('ix_satellites_id'), table_name='satellites')
    op.drop_table('satellites')
