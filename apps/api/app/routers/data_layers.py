"""Data layers: list tables and row counts for bronze, silver, gold. Optional sample rows."""
import re
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from app.database import get_db

router = APIRouter(prefix="/data-layers")

SCHEMAS = ("bronze", "silver", "gold")
TABLE_NAME_RE = re.compile(r"^[a-zA-Z0-9_]+$")


@router.get("/tables")
def list_tables(
    layer: str = Query(..., description="Layer: bronze, silver, or gold"),
    db=Depends(get_db),
):
    """GET /v1/data-layers/tables?layer=bronze - list tables in layer with row counts."""
    if layer not in SCHEMAS:
        raise HTTPException(400, f"layer must be one of: {', '.join(SCHEMAS)}")
    # List tables and approximate row counts (reltuples when available, else count(*))
    r = db.execute(text("""
        SELECT c.relname AS table_name,
               COALESCE(c.reltuples::bigint, 0) AS approx_rows
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = :schema
          AND c.relkind = 'r'
        ORDER BY c.relname
    """), {"schema": layer})
    rows = r.fetchall()
    # If approx is 0, optionally do exact count; for many tables that's slow, so we keep approx
    tables = [{"table_name": row[0], "row_count": max(0, row[1] or 0)} for row in rows]
    return {"layer": layer, "tables": tables}


@router.get("/tables/{schema_name}/{table_name}/sample")
def sample_table(
    schema_name: str,
    table_name: str,
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_db),
):
    """GET /v1/data-layers/tables/bronze/file_registry/sample?limit=10 - first N rows (safe for browsing)."""
    if schema_name not in SCHEMAS or not TABLE_NAME_RE.match(table_name):
        raise HTTPException(400, "Invalid schema or table name")
    # Check table exists
    check = db.execute(
        text("SELECT 1 FROM information_schema.tables WHERE table_schema = :s AND table_name = :t"),
        {"s": schema_name, "t": table_name},
    ).fetchone()
    if not check:
        raise HTTPException(404, f"Table {schema_name}.{table_name} not found")
    quoted = f'"{schema_name}"."{table_name}"'
    try:
        r = db.execute(text(f"SELECT * FROM {quoted} LIMIT :lim"), {"lim": limit})
        rows = r.fetchall()
        colnames = list(r.keys()) if hasattr(r, "keys") else ([f"col_{i}" for i in range(len(rows[0]))] if rows else [])
        # Serialize rows as list of dicts (handle dates/uuids)
        data = []
        for row in rows:
            data.append({colnames[i]: (v.isoformat() if hasattr(v, "isoformat") else str(v) if v is not None else None) for i, v in enumerate(row)})
        return {"schema": schema_name, "table": table_name, "columns": colnames, "rows": data}
    except Exception as e:
        raise HTTPException(500, str(e))
