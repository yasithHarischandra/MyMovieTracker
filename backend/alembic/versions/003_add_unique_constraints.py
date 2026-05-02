"""add unique constraints to seasons and episodes

Revision ID: 003_add_unique_constraints
Revises: 002_add_is_dropped
Create Date: 2026-04-29 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_add_unique_constraints'
down_revision: Union[str, None] = '002_add_is_dropped'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adding unique constraints using batch_alter_table for SQLite compatibility.
    # Note: If there are existing duplicates, this migration will fail.
    # The user should run the fix_duplicates.py script first in production.
    with op.batch_alter_table('seasons', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_season_show_number', ['show_id', 'season_number'])

    with op.batch_alter_table('episodes', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_episode_season_number', ['season_id', 'episode_number'])


def downgrade() -> None:
    with op.batch_alter_table('episodes', schema=None) as batch_op:
        batch_op.drop_constraint('uq_episode_season_number', type_='unique')

    with op.batch_alter_table('seasons', schema=None) as batch_op:
        batch_op.drop_constraint('uq_season_show_number', type_='unique')
