"""Add custom SQL website integration

Revision ID: 004
Revises: 003
Create Date: 2026-11-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'sql_websites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('website_url', sa.String(length=500), nullable=True),
        sa.Column('database_type', sa.String(length=50), nullable=False),
        sa.Column('connector_url', sa.String(length=500), nullable=False),
        sa.Column('api_token', sa.Text(), nullable=False),
        sa.Column('table_name', sa.String(length=255), nullable=True),
        sa.Column('column_mapping', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('last_tested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_test_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sql_websites_id'), 'sql_websites', ['id'], unique=False)
    op.create_index(op.f('ix_sql_websites_company_id'), 'sql_websites', ['company_id'], unique=False)

    op.create_table(
        'sql_publications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('blog_version_id', sa.Integer(), nullable=False),
        sa.Column('sql_website_id', sa.Integer(), nullable=False),
        sa.Column('source_revision', sa.Integer(), nullable=False),
        sa.Column('source_hash', sa.String(length=64), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('external_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['blog_version_id'], ['blog_versions.id'], ),
        sa.ForeignKeyConstraint(['sql_website_id'], ['sql_websites.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('blog_version_id', 'sql_website_id', name='uq_sql_publication_blog_website')
    )
    op.create_index(op.f('ix_sql_publications_id'), 'sql_publications', ['id'], unique=False)
    op.create_index(op.f('ix_sql_publications_blog_version_id'), 'sql_publications', ['blog_version_id'], unique=False)
    op.create_index(op.f('ix_sql_publications_sql_website_id'), 'sql_publications', ['sql_website_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_sql_publications_sql_website_id'), table_name='sql_publications')
    op.drop_index(op.f('ix_sql_publications_blog_version_id'), table_name='sql_publications')
    op.drop_index(op.f('ix_sql_publications_id'), table_name='sql_publications')
    op.drop_table('sql_publications')

    op.drop_index(op.f('ix_sql_websites_company_id'), table_name='sql_websites')
    op.drop_index(op.f('ix_sql_websites_id'), table_name='sql_websites')
    op.drop_table('sql_websites')
