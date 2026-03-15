from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from app.database import get_db

router = APIRouter()


@router.get("/dq/rules", response_model=dict)
def list_dq_rules(
    layer: Optional[str] = Query(None),
    table_name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db=Depends(get_db),
):
    """GET /v1/governance/dq/rules"""
    offset = (page - 1) * per_page
    params = {"limit": per_page, "offset": offset}
    where = "is_active = true"
    if layer:
        params["layer"] = layer
        where += " AND layer = :layer"
    if table_name:
        params["table_name"] = table_name
        where += " AND table_name = :table_name"
    r = db.execute(text(f"""
        SELECT rule_id, rule_name, layer, table_name, rule_type, rule_definition, severity, is_active
        FROM bronze.dq_rule
        WHERE {where}
        ORDER BY layer, table_name
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    data = [{"rule_id": str(row[0]), "rule_name": row[1], "layer": row[2], "table_name": row[3], "rule_type": row[4], "rule_definition": row[5], "severity": row[6], "is_active": row[7]} for row in rows]
    count_params = {k: v for k, v in params.items() if k in ("layer", "table_name")}
    total = db.execute(text(f"SELECT COUNT(*) FROM bronze.dq_rule WHERE {where}"), count_params).scalar() or 0
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total}, "last_updated": datetime.utcnow().isoformat() + "Z"}


@router.get("/dq/results", response_model=dict)
def list_dq_results(
    run_id: Optional[str] = Query(None),
    layer: Optional[str] = Query(None),
    table: Optional[str] = Query(None, alias="table_name"),
    passed: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db=Depends(get_db),
):
    """GET /v1/governance/dq/results?run_id=&layer=&table="""
    offset = (page - 1) * per_page
    params = {"limit": per_page, "offset": offset}
    where = "1=1"
    if run_id:
        params["run_id"] = run_id
        where += " AND run_id = :run_id"
    if layer:
        params["layer"] = layer
        where += " AND layer = :layer"
    if table:
        params["table_name"] = table
        where += " AND table_name = :table_name"
    if passed is not None:
        params["passed"] = passed
        where += " AND passed = :passed"
    r = db.execute(text(f"""
        SELECT result_id, run_id, file_id, layer, table_name, rule_id, passed, failed_count, total_count, sample_failures, created_at
        FROM bronze.dq_result
        WHERE {where}
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    data = []
    for row in rows:
        data.append({
            "result_id": str(row[0]),
            "run_id": str(row[1]) if row[1] else None,
            "file_id": str(row[2]) if row[2] else None,
            "layer": row[3],
            "table_name": row[4],
            "rule_id": str(row[5]) if row[5] else None,
            "passed": row[6],
            "failed_count": row[7],
            "total_count": row[8],
            "sample_failures": row[9],
            "created_at": row[10].isoformat() if row[10] else None,
        })
    count_params = {k: v for k, v in params.items() if k not in ("limit", "offset")}
    total = db.execute(text(f"SELECT COUNT(*) FROM bronze.dq_result WHERE {where}"), count_params).scalar() or 0
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total}, "last_updated": datetime.utcnow().isoformat() + "Z"}
