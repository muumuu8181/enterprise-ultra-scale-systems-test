"""add_social_tables

Revision ID: 568ccc8266b2
Revises: 457bbb7155a1
Create Date: 2024-05-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '568ccc8266b2'
down_revision: Union[str, None] = '457bbb7155a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Friend Requests
    op.create_table(
        'friend_requests',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('from_user_id', sa.Integer(), nullable=False),
        sa.Column('to_user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', name='friendrequeststatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['from_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['to_user_id'], ['users.id'], )
    )

    # Friendships
    op.create_table(
        'friendships',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user1_id', sa.Integer(), nullable=False),
        sa.Column('user2_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user1_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user2_id'], ['users.id'], ),
        sa.UniqueConstraint('user1_id', 'user2_id', name='uq_friendships_user1_user2')
    )

    # Gifts
    op.create_table(
        'gifts',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('from_user_id', sa.Integer(), nullable=False),
        sa.Column('to_user_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.String(), nullable=False),
        sa.Column('message', sa.String(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('claimed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['from_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['to_user_id'], ['users.id'], )
    )


def downgrade() -> None:
    op.drop_table('gifts')
    op.drop_table('friendships')
    op.drop_table('friend_requests')
    op.execute("DROP TYPE friendrequeststatus")
