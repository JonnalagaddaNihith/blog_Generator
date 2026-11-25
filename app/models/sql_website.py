"""Custom SQL website connection and publication ledger models."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class SqlDatabaseType(str, enum.Enum):
    """Supported SQL database engines (handled by the customer-side connector)."""
    mysql = "mysql"
    postgresql = "postgresql"
    mariadb = "mariadb"
    sqlite = "sqlite"
    mssql = "mssql"


class SqlWebsiteStatus(str, enum.Enum):
    """Connection test status for a custom SQL website."""
    untested = "untested"
    connected = "connected"
    error = "error"


class SqlWebsite(Base):
    """A customer's custom website reachable through a secure publishing connector.

    The connector URL points at a FastAPI connector deployed on the customer's
    backend. Database credentials never leave the customer's infrastructure;
    only the connector API token is stored here (encrypted).
    """
    __tablename__ = "sql_websites"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    website_url = Column(String(500), nullable=True)  # Public site URL for "view live" links
    database_type = Column(String(50), nullable=False)  # SqlDatabaseType value
    connector_url = Column(String(500), nullable=False)  # e.g. https://blog.example.com/api/connector
    api_token = Column(Text, nullable=False)  # Encrypted bearer token for the connector
    table_name = Column(String(255), nullable=True)  # Authorized table receiving blog rows
    column_mapping = Column(JSON, nullable=True)  # {blog_field: sql_column}
    status = Column(String(50), default=SqlWebsiteStatus.untested.value, nullable=False)
    last_tested_at = Column(DateTime(timezone=True), nullable=True)
    last_test_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Company", backref="sql_websites")
    publications = relationship("SqlPublication", back_populates="sql_website")


class SqlPublicationStatus(str, enum.Enum):
    """Status of a custom SQL publication."""
    published = "published"
    draft = "draft"
    needs_reconciliation = "needs_reconciliation"
    verify_pending = "verify_pending"
    already_published = "already_published"


class SqlPublication(Base):
    """Ledger tracking which blog versions were pushed to which custom website.

    Guarantees one ledger row per (blog_version, website) pair so repeat
    publishes update the existing remote record instead of duplicating it.
    """
    __tablename__ = "sql_publications"
    __table_args__ = (
        UniqueConstraint("blog_version_id", "sql_website_id", name="uq_sql_publication_blog_website"),
    )

    id = Column(Integer, primary_key=True, index=True)
    blog_version_id = Column(Integer, ForeignKey("blog_versions.id"), nullable=False, index=True)
    sql_website_id = Column(Integer, ForeignKey("sql_websites.id"), nullable=False, index=True)
    source_revision = Column(Integer, nullable=False)
    source_hash = Column(String(64), nullable=False)
    external_id = Column(String(255), nullable=True)  # Connector-assigned record identifier
    external_url = Column(String(500), nullable=True)  # Live URL if the site provides one
    status = Column(String(50), default=SqlPublicationStatus.published.value, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    blog_version = relationship("BlogVersion", backref="sql_publications")
    sql_website = relationship("SqlWebsite", back_populates="publications")
