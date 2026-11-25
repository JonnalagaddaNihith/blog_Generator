"""Customer-side publishing connector for Custom SQL websites.

Deploy this small FastAPI app on the website's backend (behind HTTPS,
ideally on the same host as the site or an internal admin path). It holds
the database credentials and exposes a minimal, authenticated API that the
AI Blog Generator Studio calls to push blog rows into an allow-listed table.

Endpoints:
    GET  /health                  -> connector + DB status
    GET  /tables                  -> allow-listed tables and columns
    GET  /tables/{table}/columns  -> columns of one allow-listed table
    GET  /records/lookup          -> read-only row lookup by column value
    POST /blogs/upsert            -> validated insert/update of a blog row

Security:
- Bearer-token auth (CONNECTOR_API_TOKENS env).
- Table allow-list (ALLOWED_TABLES env) — mandatory.
- Column names validated against the inspected schema; identifiers must be
  simple [A-Za-z_][A-Za-z0-9_]* names.
- All writes use SQLAlchemy Core with bound parameters inside a
  transaction — no raw SQL, no arbitrary query execution.
"""

from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from . import db, mapping
from .config import settings

app = FastAPI(
    title="Blog Publisher Connector",
    description="Secure publishing connector for custom SQL-backed websites",
    version="1.0.0",
)


def require_auth(authorization: Optional[str] = Header(default=None)) -> None:
    if not settings.tokens:
        raise HTTPException(status_code=503, detail="Connector has no API tokens configured")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(None, 1)[1].strip()
    if token not in settings.tokens:
        raise HTTPException(status_code=401, detail="Invalid API token")


@app.get("/health")
def health(_auth: None = Depends(require_auth)):
    try:
        with db.get_engine().connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unreachable: {exc}")
    return {
        "status": "ok",
        "database_type": settings.database_type,
        "version": "1.0.0",
        "message": "Connector healthy",
    }


@app.get("/tables")
def list_tables(_auth: None = Depends(require_auth)):
    try:
        tables = []
        for name in db.list_allowed_tables():
            tables.append({"name": name, "columns": db.describe_table(name)})
        return {"tables": tables}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.get("/tables/{table_name}/columns")
def table_columns(table_name: str, _auth: None = Depends(require_auth)):
    try:
        return {"table": table_name, "columns": db.describe_table(table_name)}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/records/lookup")
def records_lookup(
    table: str = Query(...),
    column: str = Query(...),
    value: str = Query(...),
    _auth: None = Depends(require_auth),
):
    try:
        record = mapping.lookup_record(table, column, value)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except (LookupError, mapping.MappingError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"record": record}


class UpsertPayload(BaseModel):
    table: str = Field(..., description="Allow-listed target table")
    column_mapping: Dict[str, str] = Field(..., description="{blog_field: sql_column}")
    record: Dict[str, Any] = Field(..., description="{blog_field: value}")
    dedupe_column: Optional[str] = Field(default=None, description="Column used to detect existing rows (usually the slug column)")
    external_id: Optional[str] = Field(default=None, description="Previously returned record id (informational)")
    status_column: Optional[str] = None
    status_value: Optional[str] = None


@app.post("/blogs/upsert")
def upsert_blog(payload: UpsertPayload, _auth: None = Depends(require_auth)):
    """Insert or update a blog row. Idempotent via dedupe_column."""
    try:
        result = mapping.upsert_blog(
            table_name=payload.table,
            column_mapping=payload.column_mapping,
            record=payload.record,
            dedupe_column=payload.dedupe_column,
            status_column=payload.status_column,
            status_value=payload.status_value,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except mapping.MappingError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database write failed: {exc}")
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.app_host, port=settings.app_port)
