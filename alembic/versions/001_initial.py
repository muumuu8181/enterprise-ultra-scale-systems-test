"""initial

Revision ID: 001
Revises:
Create Date: 2024-05-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ml_models table
    op.create_table('ml_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('artifact_uri', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ml_models_name'), 'ml_models', ['name'], unique=False)

    # experiments table
    op.create_table('experiments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # runs table
    op.create_table('runs',
        sa.Column('id', sa.String(), nullable=False), # UUID usually but string is fine
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('params', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # deployed_models table
    op.create_table('deployed_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.Integer(), nullable=False),
        sa.Column('endpoint_url', sa.String(), nullable=False),
        sa.Column('traffic_percentage', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['model_id'], ['ml_models.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # ab_tests table
    op.create_table('ab_tests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('variants', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('ab_tests')
    op.drop_table('deployed_models')
    op.drop_table('runs')
    op.drop_table('experiments')
    op.drop_index(op.f('ix_ml_models_name'), table_name='ml_models')
    op.drop_table('ml_models')
