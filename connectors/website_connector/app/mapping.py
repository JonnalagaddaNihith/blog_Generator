"""Validated blog-record mapping and upsert logic.

Safety model:
- Table names must be in the connector's ALLOWED_TABLES.
- Column names must match ^[A-Za-z_][A-Za-z0-9_]*$ AND exist in the
  inspected schema of that table.
- All statements go through SQLAlchemy Core with bound parameters —
  no string-interpolated SQL, no arbitrary query execution.
"""

import re
from typing import Any, Dict, Optional

from sqlalchemy import select, table, column

from . import db

IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class MappingError(Exception):
    """Raised when a mapping or payload fails validation."""
    pass


def _check_identifier(name: str, kind: str = "identifier") -> str:
    if not isinstance(name, str) or not IDENTIFIER_RE.match(name):
        raise MappingError(f"Invalid {kind} name: {name!r}")
    return name


def validate_table(table_name: str) -> str:
    _check_identifier(table_name, "table")
    if table_name not in db.settings.allowed_table_list:
        raise PermissionError(f"Table '{table_name}' is not in ALLOWED_TABLES")
    if table_name not in db.get_inspector().get_table_names():
        raise LookupError(f"Table '{table_name}' does not exist")
    return table_name


def _existing_columns(table_name: str) -> Dict[str, Dict[str, Any]]:
    return {c["name"]: c for c in db.describe_table(table_name)}


def build_values(
    table_name: str,
    column_mapping: Dict[str, str],
    record: Dict[str, Any],
    status_column: Optional[str] = None,
    status_value: Optional[str] = None,
) -> Dict[str, Any]:
    """Translate {blog_field: value} through the field->column mapping.

    Returns {column_name: value} containing only mapped, existing columns.
    """
    columns = _existing_columns(table_name)
    values: Dict[str, Any] = {}

    if not isinstance(column_mapping, dict) or not column_mapping:
        raise MappingError("column_mapping is required")

    for field, col_name in column_mapping.items():
        _check_identifier(col_name, "column")
        if col_name not in columns:
            raise MappingError(f"Column '{col_name}' (for field '{field}') does not exist in table '{table_name}'")
        if field in record and record[field] is not None:
            values[col_name] = record[field]

    if status_column:
        _check_identifier(status_column, "column")
        if status_column not in columns:
            raise MappingError(f"Status column '{status_column}' does not exist in table '{table_name}'")
        values[status_column] = status_value

    if not values:
        raise MappingError("No mapped values to write")
    return values


def _pk_columns(table_name: str) -> list:
    return db.get_primary_key(table_name)


def upsert_blog(
    table_name: str,
    column_mapping: Dict[str, str],
    record: Dict[str, Any],
    dedupe_column: Optional[str] = None,
    status_column: Optional[str] = None,
    status_value: Optional[str] = None,
) -> Dict[str, Any]:
    """Insert or update a blog row inside a single transaction.

    Dedupe strategy: when dedupe_column is provided and a value exists in
    the mapped record, an existing row with that value is UPDATEd; otherwise
    a new row is INSERTed. When the table has a single-column primary key,
    it is used for precise row targeting.
    """
    validate_table(table_name)
    values = build_values(table_name, column_mapping, record, status_column, status_value)

    # Resolve dedupe value: prefer explicit dedupe column, else the 'slug' field's column
    dedupe_value = None
    if dedupe_column:
        _check_identifier(dedupe_column, "column")
        slug_col = column_mapping.get("slug")
        # dedupe_column should be the SQL column that stores the slug
        for field, col in column_mapping.items():
            if col == dedupe_column and record.get(field) is not None:
                dedupe_value = record[field]
                break
        if dedupe_value is None and slug_col == dedupe_column:
            dedupe_value = record.get("slug")

    all_cols = _existing_columns(table_name)
    tbl = table(table_name, *(column(n) for n in all_cols))
    engine = db.get_engine()

    with engine.begin() as conn:
        existing_pk = None
        if dedupe_column and dedupe_value is not None:
            pk = _pk_columns(table_name)
            if pk:
                sel = select(*[tbl.c[c] for c in pk]).where(
                    tbl.c[dedupe_column] == dedupe_value
                ).limit(1)
            else:
                sel = select(tbl.c[dedupe_column]).where(
                    tbl.c[dedupe_column] == dedupe_value
                ).limit(1)
            row = conn.execute(sel).first()
            if row is not None:
                existing_pk = row[0] if pk else dedupe_value

        if existing_pk is not None:
            pk = _pk_columns(table_name)
            if pk and len(pk) == 1:
                conn.execute(
                    tbl.update().where(tbl.c[pk[0]] == existing_pk).values(**values)
                )
            else:
                conn.execute(
                    tbl.update().where(tbl.c[dedupe_column] == dedupe_value).values(**values)
                )
            action = "updated"
            external_id = str(existing_pk)
        else:
            result = conn.execute(tbl.insert().values(**values))
            action = "inserted"
            pk = _pk_columns(table_name)
            external_id = None
            if pk and len(pk) == 1:
                # Best-effort: fetch last inserted pk where supported
                try:
                    external_id = str(result.inserted_primary_key[0])
                except Exception:
                    external_id = None
            if external_id is None and dedupe_value is not None:
                external_id = str(dedupe_value)

    return {"action": action, "external_id": external_id, "url": None}


def lookup_record(table_name: str, column_name: str, value: str) -> Optional[Dict[str, Any]]:
    """Look up a single row by column value (read-only, allow-listed)."""
    validate_table(table_name)
    _check_identifier(column_name, "column")
    cols = _existing_columns(table_name)
    if column_name not in cols:
        raise MappingError(f"Column '{column_name}' does not exist in table '{table_name}'")

    tbl = table(table_name, *(column(n) for n in cols))
    engine = db.get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            select(tbl).where(tbl.c[column_name] == value).limit(1)
        ).mappings().first()
    return dict(row) if row else None
