"""add vector search

Revision ID: 002
Revises: 001
Create Date: 2024-05-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table('vector_collections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('dimension', sa.Integer(), nullable=False),
        sa.Column('metric', sa.String(), nullable=False),
        sa.Column('item_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_vector_collections_id'), 'vector_collections', ['id'], unique=False)
    op.create_index(op.f('ix_vector_collections_name'), 'vector_collections', ['name'], unique=True)

    op.create_table('vector_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('collection_id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(), nullable=False),
        sa.Column('embedding', Vector(None), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['collection_id'], ['vector_collections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vector_items_collection_id'), 'vector_items', ['collection_id'], unique=False)
    op.create_index(op.f('ix_vector_items_external_id'), 'vector_items', ['external_id'], unique=False)
    op.create_index(op.f('ix_vector_items_id'), 'vector_items', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_vector_items_id'), table_name='vector_items')
    op.drop_index(op.f('ix_vector_items_external_id'), table_name='vector_items')
    op.drop_index(op.f('ix_vector_items_collection_id'), table_name='vector_items')
    op.drop_table('vector_items')
    op.drop_index(op.f('ix_vector_collections_name'), table_name='vector_collections')
    op.drop_index(op.f('ix_vector_collections_id'), table_name='vector_collections')
    op.drop_table('vector_collections')
    op.execute("DROP EXTENSION IF EXISTS vector")
