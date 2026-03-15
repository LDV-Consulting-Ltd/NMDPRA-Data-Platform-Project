"""Shared parser utilities: type coercion, numeric/date parsing, extraction method."""
from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional, Tuple
from uuid import uuid4


EXTRACTION_METHOD_TEXT = "text"
EXTRACTION_METHOD_TABLE = "table"
EXTRACTION_METHOD_OCR = "ocr"
EXTRACTION_METHOD_CHART_TABLE = "chart_table"
PARSER_VERSION = "1.0.0"


def safe_decimal(value: Any) -> Optional[Decimal]:
    """Parse string/number to Decimal; strip commas; return None for blank/invalid."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    s = str(value).strip().replace(",", "")
    if not s or s.lower() in ("-", "n/a", "na", "nil", "—", "–"):
        return None
    try:
        return Decimal(re.sub(r"[^\d.\-]", "", s))
    except Exception:
        return None


def safe_int(value: Any) -> Optional[int]:
    """Parse to int; strip commas; return None for blank/invalid."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    s = str(value).strip().replace(",", "")
    if not s:
        return None
    try:
        return int(Decimal(s))
    except Exception:
        return None


def parse_date(value: Any) -> Optional[date]:
    """Parse YYYY-MM-DD, DD/MM/YYYY, or month name formats to date."""
    if value is None:
        return None
    if isinstance(value, date):
        return value if not isinstance(value, datetime) else value.date()
    s = str(value).strip()
    if not s:
        return None
    # YYYY-MM-DD
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    # DD/MM/YYYY or DD-MM-YYYY
    m = re.match(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", s)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass
    # YYYY-MM (month report)
    m = re.match(r"(\d{4})-(\d{2})", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), 1)
        except ValueError:
            pass
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except Exception:
        pass
    return None


def parse_month_first(value: Any) -> Optional[date]:
    """Parse to date; if only year-month, return first day of month."""
    d = parse_date(value)
    if d is None:
        return None
    return date(d.year, d.month, 1)


def uuid7() -> str:
    """Return new UUID string for primary keys."""
    return str(uuid4())


def row_meta(
    source_file_id: Optional[str],
    source_page: Optional[int],
    extraction_method: str = EXTRACTION_METHOD_TABLE,
    confidence_score: float = 0.9,
) -> dict:
    """Return standard traceability dict for a row."""
    return {
        "source_file_id": source_file_id,
        "source_page": source_page,
        "extraction_method": extraction_method,
        "confidence_score": round(confidence_score, 4),
        "parser_version": PARSER_VERSION,
    }


def normalize_product(s: Optional[str]) -> str:
    """Normalize product name (PMS, AGO, DPK, etc.)."""
    if not s or not str(s).strip():
        return "Unknown"
    return str(s).strip().upper()


def normalize_location(s: Optional[str]) -> str:
    """Normalize location name."""
    if not s or not str(s).strip():
        return "Unknown"
    return str(s).strip()
