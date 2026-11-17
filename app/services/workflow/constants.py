"""Constants for the blog generation workflow."""
import enum


class RegenerateSection(str, enum.Enum):
    """Sections that can be regenerated in the workflow."""
    OUTLINE = "outline"
    BLOG_CONTENT = "blog_content"
    SEO = "seo"
    IMAGE = "image"
    VERIFICATION = "verification"
    ALL = "all"


class WorkflowStage(str, enum.Enum):
    """Named stages in the workflow."""
    START = "start"
    WEB_RESEARCH = "web_research"
    KEYWORD_INTELLIGENCE = "keyword_intelligence"
    COMPETITOR_GAP = "competitor_gap"
    BLOG_STRATEGY = "blog_strategy"
    BLOG_STRATEGY_APPROVAL = "blog_strategy_approval"
    BLOG_WRITING = "blog_writing"
    SEO = "seo"
    IMAGE = "image"
    QUALITY = "quality"
    FACT_VERIFICATION = "fact_verification"
    FINAL_APPROVAL = "final_approval"
    REGENERATE_OUTLINE = "regenerate_outline"
    REGENERATE_SEO = "regenerate_seo"
    REGENERATE_IMAGE = "regenerate_image"
    REGENERATE_VERIFICATION = "regenerate_verification"
    REGENERATE_ALL = "regenerate_all"


class PersistenceStatus(str, enum.Enum):
    """Status of database persistence operations."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
