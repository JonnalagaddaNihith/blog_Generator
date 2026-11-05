"""Initial migration

Revision ID: 001
Revises:
Create Date: 2026-11-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create companies table
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_companies_id'), 'companies', ['id'], unique=False)
    op.create_index(op.f('ix_companies_name'), 'companies', ['name'], unique=False)

    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('topic', sa.String(length=500), nullable=False),
        sa.Column('target_word_count', sa.Integer(), nullable=False),
        sa.Column('audience', sa.Text(), nullable=True),
        sa.Column('tone', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('draft', 'in_progress', 'completed', 'failed', name='projectstatus'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)

    # Create research table
    op.create_table(
        'research',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('query', sa.String(length=1000), nullable=False),
        sa.Column('results', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_id'), 'research', ['id'], unique=False)

    # Create keywords table
    op.create_table(
        'keywords',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('primary_keywords', sa.JSON(), nullable=True),
        sa.Column('secondary_keywords', sa.JSON(), nullable=True),
        sa.Column('long_tail_keywords', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_keywords_id'), 'keywords', ['id'], unique=False)

    # Create competitor_gaps table
    op.create_table(
        'competitor_gaps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('competitors', sa.JSON(), nullable=True),
        sa.Column('gaps', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_competitor_gaps_id'), 'competitor_gaps', ['id'], unique=False)

    # Create outlines table
    op.create_table(
        'outlines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('structure', sa.JSON(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'approved', 'rejected', name='outlinestatus'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_outlines_id'), 'outlines', ['id'], unique=False)

    # Create blog_versions table
    op.create_table(
        'blog_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('outline_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'approved', 'rejected', name='blogstatus'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['outline_id'], ['outlines.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_blog_versions_id'), 'blog_versions', ['id'], unique=False)

    # Create image_generations table
    op.create_table(
        'image_generations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('blog_version_id', sa.Integer(), nullable=False),
        sa.Column('prompt', sa.String(length=2000), nullable=True),
        sa.Column('image_path', sa.String(length=500), nullable=True),
        sa.Column('model_used', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['blog_version_id'], ['blog_versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_image_generations_id'), 'image_generations', ['id'], unique=False)

    # Create seo_metadata table
    op.create_table(
        'seo_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('blog_version_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('meta_description', sa.Text(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('headings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['blog_version_id'], ['blog_versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_seo_metadata_id'), 'seo_metadata', ['id'], unique=False)

    # Create quality_reports table
    op.create_table(
        'quality_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('blog_version_id', sa.Integer(), nullable=False),
        sa.Column('grammar_score', sa.Float(), nullable=True),
        sa.Column('readability_score', sa.Float(), nullable=True),
        sa.Column('issues', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['blog_version_id'], ['blog_versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quality_reports_id'), 'quality_reports', ['id'], unique=False)

    # Create fact_verification_reports table
    op.create_table(
        'fact_verification_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('blog_version_id', sa.Integer(), nullable=False),
        sa.Column('claims_verified', sa.Integer(), nullable=True),
        sa.Column('sources', sa.JSON(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['blog_version_id'], ['blog_versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fact_verification_reports_id'), 'fact_verification_reports', ['id'], unique=False)

    # Create approvals table
    op.create_table(
        'approvals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('blog_version_id', sa.Integer(), nullable=False),
        sa.Column('stage', sa.Enum('outline', 'final', name='approvalstage'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='approvalstatus'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approver', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['blog_version_id'], ['blog_versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_approvals_id'), 'approvals', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_approvals_id'), table_name='approvals')
    op.drop_table('approvals')
    op.drop_index(op.f('ix_fact_verification_reports_id'), table_name='fact_verification_reports')
    op.drop_table('fact_verification_reports')
    op.drop_index(op.f('ix_quality_reports_id'), table_name='quality_reports')
    op.drop_table('quality_reports')
    op.drop_index(op.f('ix_seo_metadata_id'), table_name='seo_metadata')
    op.drop_table('seo_metadata')
    op.drop_index(op.f('ix_image_generations_id'), table_name='image_generations')
    op.drop_table('image_generations')
    op.drop_index(op.f('ix_blog_versions_id'), table_name='blog_versions')
    op.drop_table('blog_versions')
    op.drop_index(op.f('ix_outlines_id'), table_name='outlines')
    op.drop_table('outlines')
    op.drop_index(op.f('ix_competitor_gaps_id'), table_name='competitor_gaps')
    op.drop_table('competitor_gaps')
    op.drop_index(op.f('ix_keywords_id'), table_name='keywords')
    op.drop_table('keywords')
    op.drop_index(op.f('ix_research_id'), table_name='research')
    op.drop_table('research')
    op.drop_index(op.f('ix_projects_id'), table_name='projects')
    op.drop_table('projects')
    op.drop_index(op.f('ix_companies_name'), table_name='companies')
    op.drop_index(op.f('ix_companies_id'), table_name='companies')
    op.drop_table('companies')
