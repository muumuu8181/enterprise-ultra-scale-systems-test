"""Add guild tables

Revision ID: a1b2c3d4e5f6
Revises: 457bbb7155a1
Create Date: 2024-05-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '457bbb7155a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Guilds
    op.create_table(
        'guilds',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('leader_id', sa.Integer(), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False, default=1),
        sa.Column('exp', sa.Integer(), nullable=False, default=0),
        sa.Column('members_count', sa.Integer(), nullable=False, default=1),
        sa.Column('max_members', sa.Integer(), nullable=False, default=10),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['leader_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Guild Members
    op.create_table(
        'guild_members',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('guild_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, default='member'),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.Column('contribution_points', sa.Integer(), nullable=False, default=0),
        sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Guild Battles
    op.create_table(
        'guild_battles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('guild_a_id', sa.Integer(), nullable=False),
        sa.Column('guild_b_id', sa.Integer(), nullable=False),
        sa.Column('winner_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('scores', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['guild_a_id'], ['guilds.id'], ),
        sa.ForeignKeyConstraint(['guild_b_id'], ['guilds.id'], ),
        sa.ForeignKeyConstraint(['winner_id'], ['guilds.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('guild_battles')
    op.drop_table('guild_members')
    op.drop_table('guilds')
