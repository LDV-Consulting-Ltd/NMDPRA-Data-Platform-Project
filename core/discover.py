"""Discover PDF links from NMDPRA public pages."""
from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from typing import Any, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

NMDPRA_BASE = "https://www.nmdpra.gov.ng"


def _soup(url: str, timeout: int = 30) -> BeautifulSoup:
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def _abs(url: str, base: str = NMDPRA_BASE) -> str:
    return urljoin(base, url) if url else ""


def _infer_month_from_text(text: str) -> Optional[date]:
    """Try to infer YYYY-MM-01 from link text or filename."""
    text = (text or "").lower()
    # e.g. "January 2024", "Jan 2024", "2024-01"
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


def discover_oilgasdata(base_url: str = f"{NMDPRA_BASE}/OilGasData") -> List[dict]:
    """Scrape OilGasData page for monthly fact sheet PDF links."""
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
        })
    return out


def discover_vesselschedule(base_url: str = f"{NMDPRA_BASE}/VesselSchedule") -> List[dict]:
    """Scrape VesselSchedule page for PDF links."""
    soup = _soup(base_url)
    out = []
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
        })
    return out


def discover_dailytruckout(base_url: str = f"{NMDPRA_BASE}/DailyTruckout") -> List[dict]:
    """Scrape DailyTruckout page (archived)."""
    soup = _soup(base_url)
    out = []
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
        })
    return out


def discover_stockreport(base_url: str = f"{NMDPRA_BASE}/StockReport") -> List[dict]:
    """Scrape StockReport page (archived)."""
    soup = _soup(base_url)
    out = []
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
        })
    return out


def parse_date_from_text(text: str) -> Optional[date]:
    """Infer report_date from link text (e.g. daily report)."""
    # DD-MM-YYYY, DD/MM/YYYY, YYYY-MM-DD
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
                it.setdefault("status", "archived" if "DailyTruckout" in url or "StockReport" in url else "active")
            all_items.extend(items)
        except Exception:
            continue
    return all_items


def content_hash_bytes(data: bytes) -> str:
    """SHA256 hex digest of content."""
    return hashlib.sha256(data).hexdigest()
