"""Discover PDF links from NMDPRA public pages."""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import date, datetime
from typing import List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

NMDPRA_BASE = "https://www.nmdpra.gov.ng"
GETDOCUMENTS_URL = f"{NMDPRA_BASE}/api/General/Getdocuments"

logger = logging.getLogger(__name__)


def _http_headers() -> dict:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
    }


def _soup(url: str, timeout: int = 30) -> BeautifulSoup:
    r = requests.get(url, timeout=timeout, headers=_http_headers())
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def _abs(url: str, base: str = NMDPRA_BASE) -> str:
    return urljoin(base, url) if url else ""


def _parse_iso_datetime(raw: Optional[str]) -> Optional[datetime]:
    if not raw or not isinstance(raw, str):
        return None
    s = raw.strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _parse_display_date(raw: Optional[str]) -> Optional[date]:
    dt = _parse_iso_datetime(raw)
    return dt.date() if dt else None


def _infer_month_from_text(text: str) -> Optional[date]:
    """Try to infer YYYY-MM-01 from link text or filename."""
    text = (text or "").lower()
    months = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }
    for name, num in months.items():
        if name in text:
            y = re.search(r"20\d{2}", text)
            if y:
                return date(int(y.group(0)), num, 1)
    m = re.search(r"(\d{4})[-_](\d{2})", text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), 1)
        except ValueError:
            pass
    return None


def _items_from_getdocuments(
    document_type: str,
    source_name: str,
    source_page_url: str,
    status: str,
) -> List[dict]:
    """
    NMDPRA Blazor site loads PDF lists from this JSON API (same as the browser).
    Document types match the ?t= query used by each menu page.
    """
    r = requests.get(
        GETDOCUMENTS_URL,
        params={"t": document_type},
        timeout=120,
        headers=_http_headers(),
    )
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        return []

    seen_pdf: set[str] = set()
    out: List[dict] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        if row.get("isDeleted") or row.get("isHidden"):
            continue
        pdf_url = (row.get("documentUrl") or "").strip()
        if not pdf_url.lower().endswith(".pdf"):
            continue
        if pdf_url in seen_pdf:
            continue
        seen_pdf.add(pdf_url)

        title = (row.get("name") or "").strip() or None
        disp = _parse_display_date(row.get("displayDate"))
        added = _parse_iso_datetime(row.get("addedDate"))

        if source_name in ("oilgasdata", "vesselschedule"):
            report_date = None
            # Title usually names report month; displayDate is often upload/publish date.
            report_period = _infer_month_from_text(title or "") or (
                date(disp.year, disp.month, 1) if disp else _infer_month_from_text(pdf_url)
            )
        else:
            rd = disp or parse_date_from_text(title or pdf_url)
            report_date = rd
            report_period = date(rd.year, rd.month, 1) if rd else None

        out.append({
            "source_name": source_name,
            "source_page_url": source_page_url,
            "pdf_url": pdf_url,
            "report_title": title,
            "report_period": report_period,
            "report_date": report_date,
            "published_at": added,
            "status": status,
        })
    return out


def discover_oilgasdata(base_url: str = f"{NMDPRA_BASE}/OilGasData") -> List[dict]:
    """Oil & Gas fact sheets: API type Statistics (same list as /OilGasData in the Blazor app)."""
    items = _items_from_getdocuments("Statistics", "oilgasdata", base_url, "active")
    if items:
        return items
    return _discover_oilgasdata_html(base_url)


def _discover_oilgasdata_html(base_url: str) -> List[dict]:
    soup = _soup(base_url)
    out: List[dict] = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if not href.lower().endswith(".pdf"):
            continue
        full_url = _abs(href, base_url)
        text = (a.get_text() or "").strip()
        report_period = _infer_month_from_text(text or full_url)
        out.append({
            "source_name": "oilgasdata",
            "source_page_url": base_url,
            "pdf_url": full_url,
            "report_title": text or None,
            "report_period": report_period,
            "report_date": None,
            "published_at": None,
            "status": "active",
        })
    return out


def discover_vesselschedule(base_url: str = f"{NMDPRA_BASE}/VesselSchedule") -> List[dict]:
    items = _items_from_getdocuments("Vessel Schedule", "vesselschedule", base_url, "active")
    if items:
        return items
    return _discover_vesselschedule_html(base_url)


def _discover_vesselschedule_html(base_url: str) -> List[dict]:
    soup = _soup(base_url)
    out: List[dict] = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if not href.lower().endswith(".pdf"):
            continue
        full_url = _abs(href, base_url)
        text = (a.get_text() or "").strip()
        report_period = _infer_month_from_text(text or full_url)
        out.append({
            "source_name": "vesselschedule",
            "source_page_url": base_url,
            "pdf_url": full_url,
            "report_title": text or None,
            "report_period": report_period,
            "report_date": None,
            "published_at": None,
            "status": "active",
        })
    return out


def discover_dailytruckout(base_url: str = f"{NMDPRA_BASE}/DailyTruckout") -> List[dict]:
    items = _items_from_getdocuments("Daily Truckout", "dailytruckout", base_url, "archived")
    if items:
        return items
    return _discover_dailytruckout_html(base_url)


def _discover_dailytruckout_html(base_url: str) -> List[dict]:
    soup = _soup(base_url)
    out: List[dict] = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if not href.lower().endswith(".pdf"):
            continue
        full_url = _abs(href, base_url)
        text = (a.get_text() or "").strip()
        report_date = parse_date_from_text(text or full_url)
        report_period = date(report_date.year, report_date.month, 1) if report_date else None
        out.append({
            "source_name": "dailytruckout",
            "source_page_url": base_url,
            "pdf_url": full_url,
            "report_title": text or None,
            "report_period": report_period,
            "report_date": report_date,
            "published_at": None,
            "status": "archived",
        })
    return out


def discover_stockreport(base_url: str = f"{NMDPRA_BASE}/StockReport") -> List[dict]:
    items = _items_from_getdocuments(
        "Stock Sufficiency Report", "stockreport", base_url, "archived"
    )
    if items:
        return items
    return _discover_stockreport_html(base_url)


def _discover_stockreport_html(base_url: str) -> List[dict]:
    soup = _soup(base_url)
    out: List[dict] = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if not href.lower().endswith(".pdf"):
            continue
        full_url = _abs(href, base_url)
        text = (a.get_text() or "").strip()
        report_date = parse_date_from_text(text or full_url)
        report_period = date(report_date.year, report_date.month, 1) if report_date else None
        out.append({
            "source_name": "stockreport",
            "source_page_url": base_url,
            "pdf_url": full_url,
            "report_title": text or None,
            "report_period": report_period,
            "report_date": report_date,
            "published_at": None,
            "status": "archived",
        })
    return out


def parse_date_from_text(text: str) -> Optional[date]:
    """Infer report_date from link text (e.g. daily report)."""
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", text)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass
    return None


def discover_all() -> List[dict]:
    """Run all discover functions and return combined list of file metadata."""
    all_items: List[dict] = []
    for fn, url in [
        (discover_oilgasdata, f"{NMDPRA_BASE}/OilGasData"),
        (discover_vesselschedule, f"{NMDPRA_BASE}/VesselSchedule"),
        (discover_dailytruckout, f"{NMDPRA_BASE}/DailyTruckout"),
        (discover_stockreport, f"{NMDPRA_BASE}/StockReport"),
    ]:
        try:
            items = fn(url)
            for it in items:
                it.setdefault(
                    "status",
                    "archived" if "DailyTruckout" in url or "StockReport" in url else "active",
                )
            all_items.extend(items)
        except Exception as e:
            logger.warning("discover_all: %s failed for %s: %s", fn.__name__, url, e)
    return all_items


def content_hash_bytes(data: bytes) -> str:
    """SHA256 hex digest of content."""
    return hashlib.sha256(data).hexdigest()
