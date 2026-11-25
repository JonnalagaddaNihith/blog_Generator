"""Configuration for the customer-side publishing connector.

Copy .env.example to .env and fill in your database URL and API token.
The connector NEVER exposes raw SQL or database credentials — it only
performs validated insert/update operations against allow-listed tables.
"""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # SQLAlchemy database URL. Supported schemes:
    #   mysql+pymysql://user:pass@host:3306/db          (MySQL / MariaDB)
    #   postgresql+psycopg://user:pass@host:5432/db     (PostgreSQL)
    #   sqlite:////absolute/path/to/site.db             (SQLite)
    #   mssql+pymssql://user:pass@host:1433/db          (SQL Server)
    database_url: str

    # Bearer token(s) the Blog Generator Studio uses to authenticate.
    # Comma-separated to allow token rotation.
    connector_api_tokens: str = ""

    # Comma-separated list of tables the connector may write to.
    # REQUIRED — the connector refuses to operate without an allow-list.
    allowed_tables: str = ""

    app_host: str = "127.0.0.1"
    app_port: int = 8500

    @property
    def tokens(self) -> List[str]:
        return [t.strip() for t in self.connector_api_tokens.split(",") if t.strip()]

    @property
    def allowed_table_list(self) -> List[str]:
        return [t.strip() for t in self.allowed_tables.split(",") if t.strip()]

    @property
    def database_type(self) -> str:
        url = self.database_url.lower()
        if url.startswith("sqlite"):
            return "sqlite"
        if "postgres" in url or "postgresql" in url:
            return "postgresql"
        if "mssql" in url or "sqlserver" in url:
            return "mssql"
        if "mariadb" in url:
            return "mariadb"
        return "mysql"


settings = Settings()
