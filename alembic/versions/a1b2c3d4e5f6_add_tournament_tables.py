"""add_tournament_tables

Revision ID: a1b2c3d4e5f6
Revises: 457bbb7155a1
Create Date: 2024-05-19 12:00:00.000000

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
    # Tournaments
    op.create_table(
        'tournaments',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('game_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('format', sa.Enum('single_elim', 'double_elim', 'round_robin', 'swiss', name='tournamentformat'), nullable=False),
        sa.Column('max_participants', sa.Integer(), nullable=False),
        sa.Column('entry_fee', sa.Float(), nullable=False),
        sa.Column('prize_pool', sa.Float(), nullable=False),
        sa.Column('status', sa.Enum('registration', 'seeding', 'in_progress', 'completed', name='tournamentstatus'), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('participants', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tournaments_id'), 'tournaments', ['id'], unique=False)
    op.create_index(op.f('ix_tournaments_game_id'), 'tournaments', ['game_id'], unique=False)
    op.create_index(op.f('ix_tournaments_name'), 'tournaments', ['name'], unique=False)

    # Teams
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('captain_id', sa.Integer(), nullable=False),
        sa.Column('members', sa.JSON(), nullable=False),
        sa.Column('elo_rating', sa.Integer(), nullable=False, default=1000),
        sa.Column('wins', sa.Integer(), nullable=False, default=0),
        sa.Column('losses', sa.Integer(), nullable=False, default=0),
        sa.Column('tournament_history', sa.JSON(), nullable=False),
        sa.Column('region', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_teams_id'), 'teams', ['id'], unique=False)
    op.create_index(op.f('ix_teams_name'), 'teams', ['name'], unique=True)
    op.create_index(op.f('ix_teams_region'), 'teams', ['region'], unique=False)

    # Matches
    op.create_table(
        'matches',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('tournament_id', sa.Integer(), nullable=False),
        sa.Column('round_number', sa.Integer(), nullable=False),
        sa.Column('team_a_id', sa.Integer(), nullable=True),
        sa.Column('team_b_id', sa.Integer(), nullable=True),
        sa.Column('score_a', sa.Integer(), nullable=False, default=0),
        sa.Column('score_b', sa.Integer(), nullable=False, default=0),
        sa.Column('winner_id', sa.Integer(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('stream_url', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('scheduled', 'live', 'completed', name='matchstatus'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tournament_id'], ['tournaments.id'], ),
        sa.ForeignKeyConstraint(['team_a_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['team_b_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['winner_id'], ['teams.id'], )
    )
    op.create_index(op.f('ix_matches_id'), 'matches', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_matches_id'), table_name='matches')
    op.drop_table('matches')

    op.drop_index(op.f('ix_teams_region'), table_name='teams')
    op.drop_index(op.f('ix_teams_name'), table_name='teams')
    op.drop_index(op.f('ix_teams_id'), table_name='teams')
    op.drop_table('teams')

    op.drop_index(op.f('ix_tournaments_name'), table_name='tournaments')
    op.drop_index(op.f('ix_tournaments_game_id'), table_name='tournaments')
    op.drop_index(op.f('ix_tournaments_id'), table_name='tournaments')
    op.drop_table('tournaments')

    op.execute("DROP TYPE IF EXISTS matchstatus")
    op.execute("DROP TYPE IF EXISTS tournamentstatus")
    op.execute("DROP TYPE IF EXISTS tournamentformat")
