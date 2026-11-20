"""Add WordPress integration

Revision ID: 002
Revises: 001
Create Date: 2026-11-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add WordPress credential columns to companies table
    op.add_column('companies', sa.Column('wp_site', sa.String(length=500), nullable=True))
    op.add_column('companies', sa.Column('wp_client_id', sa.String(length=255), nullable=True))
    op.add_column('companies', sa.Column('wp_client_secret', sa.String(length=500), nullable=True))
    op.add_column('companies', sa.Column('wp_token', sa.Text(), nullable=True))
    op.add_column('companies', sa.Column('wp_redirect_uri', sa.String(length=500), nullable=True))

    # Create wordpress_publications table
    op.create_table(
        'wordpress_publications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('blog_version_id', sa.Integer(), nullable=False),
        sa.Column('source_revision', sa.Integer(), nullable=False),
        sa.Column('source_hash', sa.String(length=64), nullable=False),
        sa.Column('wp_post_id', sa.Integer(), nullable=True),
        sa.Column('wp_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.Enum('published', 'draft', 'needs_reconciliation', 'verify_pending', 'already_published', name='publicationstatus'), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['blog_version_id'], ['blog_versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wordpress_publications_blog_version_id'), 'wordpress_publications', ['blog_version_id'], unique=False)
    op.create_index(op.f('ix_wordpress_publications_id'), 'wordpress_publications', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_wordpress_publications_id'), table_name='wordpress_publications')
    op.drop_index(op.f('ix_wordpress_publications_blog_version_id'), table_name='wordpress_publications')
    op.drop_table('wordpress_publications')
    
    op.drop_column('companies', 'wp_redirect_uri')
    op.drop_column('companies', 'wp_token')
    op.drop_column('companies', 'wp_client_secret')
    op.drop_column('companies', 'wp_client_id')
    op.drop_column('companies', 'wp_site')
