from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from app.database import get_db
from app.schemas import ReportSummary, ReportDetail, CoverageInfo, PaginatedMeta

router = APIRouter()


def _row_to_report(row) -> dict:
    return {
        "file_id": str(row[0]),
        "source_name": row[1],
        "source_page_url": row[2],
        "pdf_url": row[3],
        "report_title": row[4],
        "report_period": row[5],
        "report_date": row[6],
        "published_at": row[7],
        "content_hash": row[8],
        "file_path": row[9],
        "status": row[10],
        "discovered_at": row[11],
        "downloaded_at": row[12],
    }


@router.get("/reports", response_model=dict)
def list_reports(
    source_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    """GET /v1/reports with optional filters and pagination."""
    offset = (page - 1) * per_page
    where = ["1=1"]
    params = {"limit": per_page, "offset": offset}
    if source_name:
        where.append("source_name = :source_name")
        params["source_name"] = source_name
    if status:
        where.append("status = :status")
        params["status"] = status
    w = " AND ".join(where)
    r = db.execute(text(f"""
        SELECT file_id, source_name, source_page_url, pdf_url, report_title, report_period,
               report_date, published_at, content_hash, file_path, status, discovered_at, downloaded_at
        FROM bronze.file_registry
        WHERE {w}
        ORDER BY discovered_at DESC
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    total = db.execute(text(f"SELECT COUNT(*) FROM bronze.file_registry WHERE {w}"), {k: v for k, v in params.items() if k in ("source_name", "status")}).scalar() or 0
    data = [_row_to_report(row) for row in rows]
    for d in data:
        d["report_period"] = d["report_period"].isoformat() if d.get("report_period") else None
        d["report_date"] = d["report_date"].isoformat() if d.get("report_date") else None
        d["discovered_at"] = d["discovered_at"].isoformat() if d.get("discovered_at") else None
        d["downloaded_at"] = d["downloaded_at"].isoformat() if d.get("downloaded_at") else None
        d["published_at"] = d["published_at"].isoformat() if d.get("published_at") else None
    return {
        "data": data,
        "meta": {"page": page, "per_page": per_page, "total": total, "total_pages": (total + per_page - 1) // per_page},
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/reports/{file_id}", response_model=dict)
def get_report(file_id: str, db=Depends(get_db)):
    """GET /v1/reports/{file_id}."""
    r = db.execute(text("""
        SELECT file_id, source_name, source_page_url, pdf_url, report_title, report_period,
               report_date, published_at, content_hash, file_path, status, discovered_at, downloaded_at
        FROM bronze.file_registry WHERE file_id = :file_id
    """), {"file_id": file_id})
    row = r.fetchone()
    if not row:
        return {"data": None, "error": "Not found"}
    d = _row_to_report(row)
    for k in ("report_period", "report_date", "discovered_at", "downloaded_at", "published_at"):
        if d.get(k):
            d[k] = d[k].isoformat() if hasattr(d[k], "isoformat") else d[k]
    return {"data": d, "last_updated": datetime.utcnow().isoformat() + "Z"}


# Expected NMDPRA report sources — shown in Governance when no files downloaded yet
COVERAGE_EXPECTED_SOURCES = [
    "oilgasdata",
    "vesselschedule",
    "dailytruckout",
    "stockreport",
]


@router.get("/coverage", response_model=dict)
def coverage(db=Depends(get_db)):
    """GET /v1/coverage - coverage per dataset + last updated. When no downloads, returns expected sources with data_status no_data."""
    r = db.execute(text("""
        SELECT source_name, status, MIN(report_period) as min_period, MAX(report_period) as max_period,
               MAX(downloaded_at) as last_downloaded
        FROM bronze.file_registry
        WHERE downloaded_at IS NOT NULL
        GROUP BY source_name, status
    """))
    rows = r.fetchall()
    data = []
    seen_sources = set()
    for row in rows:
        seen_sources.add(row[0])
        data.append({
            "source_name": row[0],
            "data_status": row[1],
            "min_period": row[2].isoformat() if row[2] else None,
            "max_period": row[3].isoformat() if row[3] else None,
            "last_updated": row[4].isoformat() if row[4] else None,
        })
    # When no (or partial) data, ensure expected sources appear with no_data so Governance shows something
    for src in COVERAGE_EXPECTED_SOURCES:
        if src not in seen_sources:
            data.append({
                "source_name": src,
                "data_status": "no_data",
                "min_period": None,
                "max_period": None,
                "last_updated": None,
            })
    # Sort so no_data sources are grouped after those with data
    data.sort(key=lambda x: (0 if x["data_status"] != "no_data" else 1, x["source_name"]))
    return {"data": data, "last_updated": datetime.utcnow().isoformat() + "Z"}
