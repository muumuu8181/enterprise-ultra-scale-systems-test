"""pvp_migration

Revision ID: a1b2c3d4e5f6
Revises: 457bbb7155a1
Create Date: 2024-05-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '457bbb7155a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create Enums if not exists (handled by checkfirst in some versions, but better safe)
    # Note: Alembic + SQLAlchemy usually handles Enum creation when create_table is called
    # if the Enum is named.

    op.create_table(
        'matches',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('player1_id', sa.Integer(), nullable=False),
        sa.Column('player2_id', sa.Integer(), nullable=False),
        sa.Column('mode', sa.Enum('RANKED', 'CASUAL', name='matchmode'), nullable=False),
        sa.Column('winner_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'ACTIVE', 'COMPLETED', 'CANCELLED', name='matchstatus'), nullable=False),
        sa.Column('duration_sec', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['player1_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['player2_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['winner_id'], ['users.id'], )
    )

    op.create_table(
        'player_ratings',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('mode', sa.Enum('RANKED', 'CASUAL', name='matchmode'), nullable=False),
        sa.Column('elo_rating', sa.Integer(), nullable=False, default=1200),
        sa.Column('wins', sa.Integer(), nullable=False, default=0),
        sa.Column('losses', sa.Integer(), nullable=False, default=0),
        sa.Column('draws', sa.Integer(), nullable=False, default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )


def downgrade() -> None:
    op.drop_table('player_ratings')
    op.drop_table('matches')

    # Drop types
    op.execute("DROP TYPE matchstatus")
    op.execute("DROP TYPE matchmode")
