"""Add draft status to publication enum

Revision ID: 003
Revises: 002
Create Date: 2026-11-20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'draft' to the publicationstatus enum
    # PostgreSQL requires recreating the enum type
    op.execute("ALTER TYPE publicationstatus ADD VALUE IF NOT EXISTS 'draft'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values easily
    # This is a no-op for safety
    pass
