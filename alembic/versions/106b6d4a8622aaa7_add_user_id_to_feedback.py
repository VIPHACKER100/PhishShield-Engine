"""Add user_id to feedback table

Revision ID: 106b6d4a8622aaa7
Revises: 8eb220da558a8768
Create Date: 2026-09-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '106b6d4a8622aaa7'
down_revision: Union[str, Sequence[str], None] = '8eb220da558a8768'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add user_id foreign key column to feedback table."""
    op.add_column('feedback', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_feedback_user_id', 'feedback', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    """Remove user_id column from feedback table."""
    op.drop_constraint('fk_feedback_user_id', table_name='feedback', type_='foreignkey')
    op.drop_column('feedback', 'user_id')
