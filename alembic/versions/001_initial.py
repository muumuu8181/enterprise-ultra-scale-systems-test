"""initial

Revision ID: 001
Revises:
Create Date: 2024-05-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography
import datetime

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostGIS extension
    # We use IF NOT EXISTS to avoid errors if it's already installed
    # Also wrap in try/except because if this runs against TimescaleDB image (without postgis), it might fail
    try:
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    except Exception as e:
        print(f"Warning: Could not create postgis extension: {e}")

    # Sensors table
    # Requires PostGIS type, so this might fail if PostGIS extension failed.
    # But we define it anyway.
    try:
        op.create_table(
            'sensors',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('type', sa.String(), nullable=False),  # e.g., 'traffic', 'air_quality'
            sa.Column('location', Geography(geometry_type='POINT', srid=4326), nullable=False),
            sa.Column('status', sa.String(), default='active'),
            sa.Column('last_updated', sa.DateTime(), default=datetime.datetime.utcnow)
        )
    except Exception as e:
        print(f"Warning: Could not create sensors table (maybe missing PostGIS?): {e}")

    # Sensor Readings table (Hypertable)
    # Using 'time' as the partitioning column
    # Removed ForeignKey to decouple from sensors table location
    op.create_table(
        'sensor_readings',
        sa.Column('time', sa.DateTime(), nullable=False),
        sa.Column('sensor_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('time', 'sensor_id')
    )

    # Convert to hypertable if TimescaleDB extension is available
    # We catch the exception if the function doesn't exist (e.g., standard Postgres)
    try:
        op.execute("SELECT create_hypertable('sensor_readings', 'time', if_not_exists => TRUE)")
    except Exception as e:
        print(f"Warning: Could not create hypertable: {e}")

    # Alerts
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), default=datetime.datetime.utcnow),
        sa.Column('is_resolved', sa.Boolean(), default=False)
    )

    # Traffic Signals
    try:
        op.create_table(
            'traffic_signals',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('location', Geography(geometry_type='POINT', srid=4326), nullable=False),
            sa.Column('status', sa.String(), default='red'),
            sa.Column('intersection_id', sa.String(), nullable=True)
        )
    except Exception as e:
         print(f"Warning: Could not create traffic_signals table: {e}")

    # Emergency Incidents
    try:
        op.create_table(
            'emergency_incidents',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('type', sa.String(), nullable=False),
            sa.Column('location', Geography(geometry_type='POINT', srid=4326), nullable=False),
            sa.Column('status', sa.String(), default='reported'),
            sa.Column('reported_at', sa.DateTime(), default=datetime.datetime.utcnow)
        )
    except Exception as e:
         print(f"Warning: Could not create emergency_incidents table: {e}")


def downgrade() -> None:
    # Use try-except to avoid errors if table doesn't exist
    try: op.drop_table('emergency_incidents')
    except: pass
    try: op.drop_table('traffic_signals')
    except: pass
    try: op.drop_table('alerts')
    except: pass
    try: op.drop_table('sensor_readings')
    except: pass
    try: op.drop_table('sensors')
    except: pass
    # op.execute("DROP EXTENSION IF EXISTS postgis") # Optional
