"""Initial migration

Revision ID: 00a74f3abd5c
Revises: db7ad1f571d5
Create Date: 2026-09-15 10:43:07.232216

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00a74f3abd5c'
down_revision: Union[str, Sequence[str], None] = 'db7ad1f571d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
