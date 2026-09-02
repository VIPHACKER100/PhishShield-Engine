"""Add auth security fields to users table

Adds the following columns to support:
  - Account lockout (failed_login_attempts, locked_until)
  - Secure password reset (password_reset_token_hash, password_reset_expires)
  - Email verification (email, is_email_verified)

Revision ID: 8eb220da558a8768
Revises: 464e76178561
Create Date: 2026-09-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8eb220da558a8768'
down_revision: Union[str, Sequence[str], None] = '464e76178561'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add security columns to the users table."""
    # Email address (nullable; used for password reset delivery)
    op.add_column('users', sa.Column('email', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Email verification flag
    op.add_column('users', sa.Column(
        'is_email_verified', sa.Boolean(), nullable=False, server_default=sa.false()
    ))

    # Failed login counter — reset on successful authentication
    op.add_column('users', sa.Column(
        'failed_login_attempts', sa.Integer(), nullable=False, server_default='0'
    ))

    # Lockout expiry timestamp (UTC); NULL means the account is not locked
    op.add_column('users', sa.Column('locked_until', sa.DateTime(), nullable=True))

    # SHA-256 hash of the one-time password-reset token (raw token is never stored)
    op.add_column('users', sa.Column('password_reset_token_hash', sa.String(), nullable=True))

    # Expiry for the password-reset token
    op.add_column('users', sa.Column('password_reset_expires', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove security columns from the users table."""
    op.drop_column('users', 'password_reset_expires')
    op.drop_column('users', 'password_reset_token_hash')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'is_email_verified')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_column('users', 'email')
