"""Initial database setup

Revision ID: 968ea4a0af51
Revises:
Create Date: 2025-08-10 12:14:36.903782

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "968ea4a0af51"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgx_ulid"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    op.execute("SET timezone = 'UTC'")


def downgrade() -> None:
    """Downgrade schema."""
