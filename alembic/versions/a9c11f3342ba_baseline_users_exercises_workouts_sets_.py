"""baseline: users, exercises, workouts, sets, exercise_catalog

Revision ID: a9c11f3342ba
Revises:
Create Date: 2026-08-18 21:03:05.026082

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9c11f3342ba'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('google_sub', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('picture', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_google_sub', 'users', ['google_sub'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'])

    op.create_table(
        'exercise_catalog',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('external_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('muscle_group', sa.String(), nullable=True),
        sa.Column('primary_muscles', sa.String(), nullable=True),
        sa.Column('secondary_muscles', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('equipment', sa.String(), nullable=True),
        sa.Column('level', sa.String(), nullable=True),
        sa.Column('mechanic', sa.String(), nullable=True),
        sa.Column('force', sa.String(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('image_url_2', sa.String(), nullable=True),
    )
    op.create_index('ix_exercise_catalog_id', 'exercise_catalog', ['id'])
    op.create_index('ix_exercise_catalog_external_id', 'exercise_catalog', ['external_id'], unique=True)
    op.create_index('ix_exercise_catalog_name', 'exercise_catalog', ['name'])
    op.create_index('ix_exercise_catalog_category', 'exercise_catalog', ['category'])
    op.create_index('ix_exercise_catalog_equipment', 'exercise_catalog', ['equipment'])
    op.create_index('ix_exercise_catalog_muscle_group', 'exercise_catalog', ['muscle_group'])

    op.create_table(
        'exercises',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('muscle_group', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.UniqueConstraint('user_id', 'name', name='ix_exercises_user_id_name'),
    )
    op.create_index('ix_exercises_id', 'exercises', ['id'])
    op.create_index('ix_exercises_name', 'exercises', ['name'])
    op.create_index('ix_exercises_muscle_group', 'exercises', ['muscle_group'])
    op.create_index('ix_exercises_user_id', 'exercises', ['user_id'])

    op.create_table(
        'workouts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('bodyweight', sa.Float(), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
    )
    op.create_index('ix_workouts_id', 'workouts', ['id'])
    op.create_index('ix_workouts_date', 'workouts', ['date'])
    op.create_index('ix_workouts_user_id', 'workouts', ['user_id'])

    op.create_table(
        'sets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('workout_id', sa.Integer(), sa.ForeignKey('workouts.id'), nullable=False),
        sa.Column('exercise_id', sa.Integer(), sa.ForeignKey('exercises.id'), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('reps', sa.Integer(), nullable=False),
        sa.Column('rpe', sa.Float(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
    )
    op.create_index('ix_sets_id', 'sets', ['id'])
    op.create_index('ix_sets_workout_id', 'sets', ['workout_id'])
    op.create_index('ix_sets_exercise_id', 'sets', ['exercise_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('sets')
    op.drop_table('workouts')
    op.drop_table('exercises')
    op.drop_table('exercise_catalog')
    op.drop_table('users')
