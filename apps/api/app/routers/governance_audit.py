from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from app.database import get_db

router = APIRouter()


@router.get("/audit/api", response_model=dict)
def api_audit_log(
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = Query(None),
    path: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db=Depends(get_db),
):
    """GET /v1/governance/audit/api?from=&to=&path="""
    offset = (page - 1) * per_page
    params = {"limit": per_page, "offset": offset}
    where = "1=1"
    if from_:
        params["from"] = from_
        where += " AND created_at >= :from::timestamp"
    if to:
        params["to"] = to
        where += " AND created_at <= :to::timestamp"
    if path:
        params["path"] = f"%{path}%"
        where += " AND path ILIKE :path"
    r = db.execute(text(f"""
        SELECT id, request_id, path, method, user_agent, query_params, response_status, duration_ms, created_at
        FROM meta.api_audit_log
        WHERE {where}
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    data = []
    for row in rows:
        data.append({
            "id": str(row[0]),
            "request_id": row[1],
            "path": row[2],
            "method": row[3],
            "user_agent": row[4],
            "query_params": row[5],
            "response_status": row[6],
            "duration_ms": row[7],
            "created_at": row[8].isoformat() if row[8] else None,
        })
    count_params = {k: v for k, v in params.items() if k not in ("limit", "offset")}
    total = db.execute(text(f"SELECT COUNT(*) FROM meta.api_audit_log WHERE {where}"), count_params).scalar() or 0
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total}, "last_updated": datetime.utcnow().isoformat() + "Z"}
