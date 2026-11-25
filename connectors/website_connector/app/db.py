"""SQLAlchemy engine and schema inspection helpers (synchronous)."""

from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, inspect, select, table, column
from sqlalchemy.engine import Engine

from .config import settings

_engine: Optional[Engine] = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
    return _engine


def get_inspector() -> Any:
    return inspect(get_engine())


def list_allowed_tables() -> List[str]:
    allowed = settings.allowed_table_list
    if not allowed:
        raise RuntimeError("ALLOWED_TABLES is not configured on the connector")
    insp = get_inspector()
    existing = set(insp.get_table_names())
    missing = [t for t in allowed if t not in existing]
    if missing:
        raise RuntimeError(f"Allowed tables not found in database: {', '.join(missing)}")
    return allowed


def describe_table(table_name: str) -> List[Dict[str, Any]]:
    """Return column metadata for an allow-listed table."""
    if table_name not in settings.allowed_table_list:
        raise PermissionError(f"Table '{table_name}' is not in ALLOWED_TABLES")
    insp = get_inspector()
    if table_name not in insp.get_table_names():
        raise LookupError(f"Table '{table_name}' does not exist")
    columns = []
    for col in insp.get_columns(table_name):
        columns.append({
            "name": col["name"],
            "type": str(col["type"]),
            "nullable": col.get("nullable", True),
        })
    return columns


def get_primary_key(table_name: str) -> List[str]:
    insp = get_inspector()
    return insp.get_pk_constraint(table_name).get("constrained_columns", [])
