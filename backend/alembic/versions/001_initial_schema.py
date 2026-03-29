"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-03-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── USERS ──────────────────────────────────────────────────────────── 
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # ── MOVIES ───────────────────────────────────────────────────────────
    op.create_table('movies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tmdb_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('overview', sa.String(length=5000), nullable=True),
        sa.Column('release_date', sa.Date(), nullable=True),
        sa.Column('runtime_mins', sa.Integer(), nullable=True),
        sa.Column('genres', sa.String(length=500), nullable=True),
        sa.Column('poster_path', sa.String(length=500), nullable=True),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tmdb_id', 'user_id', name='uq_movie_tmdb_user')
    )
    op.create_index(op.f('ix_movies_id'), 'movies', ['id'], unique=False)
    op.create_index(op.f('ix_movies_tmdb_id'), 'movies', ['tmdb_id'], unique=False)
    op.create_index(op.f('ix_movies_user_id'), 'movies', ['user_id'], unique=False)

    # ── TV SHOWS ─────────────────────────────────────────────────────────
    op.create_table('tv_shows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tmdb_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('overview', sa.String(length=5000), nullable=True),
        sa.Column('first_air_date', sa.Date(), nullable=True),
        sa.Column('genres', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=100), nullable=True),
        sa.Column('poster_path', sa.String(length=500), nullable=True),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tmdb_id', 'user_id', name='uq_show_tmdb_user')
    )
    op.create_index(op.f('ix_tv_shows_id'), 'tv_shows', ['id'], unique=False)
    op.create_index(op.f('ix_tv_shows_tmdb_id'), 'tv_shows', ['tmdb_id'], unique=False)
    op.create_index(op.f('ix_tv_shows_user_id'), 'tv_shows', ['user_id'], unique=False)

    # ── SEASONS ──────────────────────────────────────────────────────────
    op.create_table('seasons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('show_id', sa.Integer(), nullable=False),
        sa.Column('season_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=True),
        sa.Column('episode_count', sa.Integer(), nullable=False),
        sa.Column('air_date', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['show_id'], ['tv_shows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_seasons_id'), 'seasons', ['id'], unique=False)
    op.create_index(op.f('ix_seasons_show_id'), 'seasons', ['show_id'], unique=False)

    # ── EPISODES ─────────────────────────────────────────────────────────
    op.create_table('episodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('season_id', sa.Integer(), nullable=False),
        sa.Column('episode_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=True),
        sa.Column('runtime_mins', sa.Integer(), nullable=True),
        sa.Column('air_date', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['season_id'], ['seasons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_episodes_id'), 'episodes', ['id'], unique=False)
    op.create_index(op.f('ix_episodes_season_id'), 'episodes', ['season_id'], unique=False)

    # ── WATCH HISTORY ────────────────────────────────────────────────────
    op.create_table('watch_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('movie_id', sa.Integer(), nullable=True),
        sa.Column('episode_id', sa.Integer(), nullable=True),
        sa.Column('watched_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.CheckConstraint('(movie_id IS NOT NULL AND episode_id IS NULL) OR (movie_id IS NULL AND episode_id IS NOT NULL)', name='ck_watch_history_one_media_type'),
        sa.ForeignKeyConstraint(['episode_id'], ['episodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['movie_id'], ['movies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_watch_history_episode_id'), 'watch_history', ['episode_id'], unique=False)
    op.create_index(op.f('ix_watch_history_id'), 'watch_history', ['id'], unique=False)
    op.create_index(op.f('ix_watch_history_movie_id'), 'watch_history', ['movie_id'], unique=False)
    op.create_index(op.f('ix_watch_history_user_id'), 'watch_history', ['user_id'], unique=False)
    op.create_index(op.f('ix_watch_history_watched_at'), 'watch_history', ['watched_at'], unique=False)


def downgrade() -> None:
    op.drop_table('watch_history')
    op.drop_table('episodes')
    op.drop_table('seasons')
    op.drop_table('tv_shows')
    op.drop_table('movies')
    op.drop_table('users')
