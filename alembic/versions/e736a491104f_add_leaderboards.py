"""add_leaderboards

Revision ID: e736a491104f
Revises: cd1b1f2dbb15
Create Date: 2026-02-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e736a491104f'
down_revision: Union[str, Sequence[str], None] = 'cd1b1f2dbb15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # global_leaderboards
    op.create_table('global_leaderboards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.String(), nullable=True),
        sa.Column('period', sa.String(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_global_leaderboards_game_id'), 'global_leaderboards', ['game_id'], unique=False)
    op.create_index(op.f('ix_global_leaderboards_id'), 'global_leaderboards', ['id'], unique=False)

    # leaderboard_entries
    op.create_table('leaderboard_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('leaderboard_id', sa.Integer(), nullable=True),
        sa.Column('player_id', sa.String(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('rank_change', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['leaderboard_id'], ['global_leaderboards.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leaderboard_entries_id'), 'leaderboard_entries', ['id'], unique=False)
    op.create_index(op.f('ix_leaderboard_entries_player_id'), 'leaderboard_entries', ['player_id'], unique=False)

    # player_stats
    op.create_table('player_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.String(), nullable=True),
        sa.Column('game_id', sa.String(), nullable=True),
        sa.Column('total_playtime_hrs', sa.Float(), nullable=True),
        sa.Column('highest_score', sa.Float(), nullable=True),
        sa.Column('matches_won', sa.Integer(), nullable=True),
        sa.Column('matches_lost', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_player_stats_game_id'), 'player_stats', ['game_id'], unique=False)
    op.create_index(op.f('ix_player_stats_id'), 'player_stats', ['id'], unique=False)
    op.create_index(op.f('ix_player_stats_player_id'), 'player_stats', ['player_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_player_stats_player_id'), table_name='player_stats')
    op.drop_index(op.f('ix_player_stats_id'), table_name='player_stats')
    op.drop_index(op.f('ix_player_stats_game_id'), table_name='player_stats')
    op.drop_table('player_stats')
    op.drop_index(op.f('ix_leaderboard_entries_player_id'), table_name='leaderboard_entries')
    op.drop_index(op.f('ix_leaderboard_entries_id'), table_name='leaderboard_entries')
    op.drop_table('leaderboard_entries')
    op.drop_index(op.f('ix_global_leaderboards_id'), table_name='global_leaderboards')
    op.drop_index(op.f('ix_global_leaderboards_game_id'), table_name='global_leaderboards')
    op.drop_table('global_leaderboards')
