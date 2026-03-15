from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from app.database import get_db

router = APIRouter()


@router.get("/vessels/clearance", response_model=dict)
def vessels_clearance(
    month: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    vessel: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db=Depends(get_db),
):
    """GET /v1/vessels/clearance?month=&company=&vessel="""
    offset = (page - 1) * per_page
    params = {"limit": per_page, "offset": offset}
    where = "1=1"
    if month:
        where += " AND date_trunc('month', report_period) = date_trunc('month', :month::date)"
        params["month"] = month + "-01" if len(month) == 7 else month
    if company:
        params["company"] = f"%{company}%"
        where += " AND company ILIKE :company"
    if vessel:
        params["vessel"] = f"%{vessel}%"
        where += " AND vessel_name ILIKE :vessel"
    r = db.execute(text(f"""
        SELECT report_period, clearance_no, company, vessel_name, initial_submission_ts, final_submission_ts,
               clearance_ts, processing_days, processing_hours, remarks
        FROM bronze.vessel_clearance_schedule
        WHERE {where}
        ORDER BY report_period DESC, clearance_ts DESC NULLS LAST
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    data = []
    for row in rows:
        data.append({
            "report_period": row[0].isoformat() if row[0] else None,
            "clearance_no": row[1],
            "company": row[2],
            "vessel_name": row[3],
            "initial_submission_ts": row[4].isoformat() if row[4] else None,
            "final_submission_ts": row[5].isoformat() if row[5] else None,
            "clearance_ts": row[6].isoformat() if row[6] else None,
            "processing_days": float(row[7]) if row[7] is not None else None,
            "processing_hours": float(row[8]) if row[8] is not None else None,
            "remarks": row[9],
        })
    total = db.execute(text(f"SELECT COUNT(*) FROM bronze.vessel_clearance_schedule WHERE {where}"), {k: v for k, v in params.items() if k not in ("limit", "offset")}).scalar() or 0
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total}, "data_status": "active", "last_updated": datetime.utcnow().isoformat() + "Z"}
