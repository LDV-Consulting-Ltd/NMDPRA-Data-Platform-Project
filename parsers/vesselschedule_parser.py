"""Parse Vessel Clearance Schedule PDFs into bronze.vessel_clearance_schedule."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import pdfplumber

from parsers.utils import (
    EXTRACTION_METHOD_TABLE,
    PARSER_VERSION,
    safe_decimal,
    parse_date,
    parse_month_first,
    row_meta,
)


def _tables(page: Any) -> List[List[List[str]]]:
    out = []
    for t in page.extract_tables() or []:
        if t and any(cell for row in t for cell in (row or []) if cell):
            out.append(t)
    return out


def _parse_ts(s: Optional[str]) -> Optional[datetime]:
    if not s or not str(s).strip():
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s[:19] if len(s) > 19 else s, fmt)
        except ValueError:
            continue
    return None


def parse_vessel_clearance_schedule(
    pages: List[Tuple[int, Any]],
    file_id: str,
    report_period: Optional[date],
) -> List[Dict[str, Any]]:
    """Extract vessel clearance rows: clearance_no, company, vessel_name, timestamps, processing_days/hours."""
    rows = []
    for page_num, page in pages:
        for table in _tables(page):
            if len(table) < 2:
                continue
            headers = [str(h).strip().lower() for h in (table[0] or [])]
            for r in table[1:]:
                if not r or not any(r):
                    continue
                r = (r or []) + [None] * max(0, 12 - len(r))
                clearance_no = str(r[0]).strip() if r[0] else None
                company = str(r[1]).strip() if len(r) > 1 and r[1] else None
                vessel = str(r[2]).strip() if len(r) > 2 and r[2] else None
                if not clearance_no and not company and not vessel:
                    continue
                period = report_period or parse_month_first(str(r[3]) if len(r) > 3 else None)
                rows.append({
                    "id": str(uuid4()),
                    "report_period": period,
                    "clearance_no": clearance_no,
                    "company": company,
                    "vessel_name": vessel,
                    "initial_submission_ts": _parse_ts(str(r[4]) if len(r) > 4 and r[4] else None),
                    "final_submission_ts": _parse_ts(str(r[5]) if len(r) > 5 and r[5] else None),
                    "clearance_ts": _parse_ts(str(r[6]) if len(r) > 6 and r[6] else None),
                    "processing_days": safe_decimal(r[7]) if len(r) > 7 else safe_decimal(r[8]),
                    "processing_hours": safe_decimal(r[8]) if len(r) > 8 else safe_decimal(r[9]),
                    "remarks": str(r[10]).strip() if len(r) > 10 and r[10] else None,
                    "source_file_id": file_id,
                    "source_page": page_num,
                    **row_meta(file_id, page_num, EXTRACTION_METHOD_TABLE, 0.8),
                })
    return rows


def parse_vesselschedule_pdf(
    pdf_path: Path,
    file_id: str,
    report_period: Optional[date] = None,
) -> Dict[str, Any]:
    """Full parse of one Vessel Schedule PDF."""
    pages_list: List[Tuple[int, Any]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, p in enumerate(pdf.pages):
            pages_list.append((i + 1, p))
    month = report_period or parse_month_first(pdf_path.stem)
    vessel_rows = parse_vessel_clearance_schedule(pages_list, file_id, month)
    return {
        "vessel_clearance_schedule": vessel_rows,
        "extraction_method": EXTRACTION_METHOD_TABLE,
        "confidence_score": 0.8,
        "parser_version": PARSER_VERSION,
    }
