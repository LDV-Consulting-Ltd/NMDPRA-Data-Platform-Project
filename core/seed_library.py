"""
Library seed: enough data to run analysis by time granularity.
- Monthly tables: past 2 years (24 months).
- Daily tables: 2 years coverage with one row per month (24 rows).
- Yearly: past 3 years if we add yearly tables later.
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import List, Tuple


def months_back(n: int, end: date | None = None) -> List[date]:
    """First-of-month dates for the past n months. End defaults to today."""
    end = end or date.today()
    out: List[date] = []
    # End month as first-of-month
    y, m = end.year, end.month
    for _ in range(n):
        out.append(date(y, m, 1))
        m -= 1
        if m < 1:
            m += 12
            y -= 1
    return out


def daily_sample_over_months(months: List[date], day_of_month: int = 15) -> List[date]:
    """One date per month (e.g. 15th) for 2 years coverage."""
    out: List[date] = []
    for m in months:
        try:
            out.append(date(m.year, m.month, min(day_of_month, 28)))
        except ValueError:
            out.append(date(m.year, m.month, 28))
    return out


# Default: 24 months (2 years) for monthly granularity
LIBRARY_MONTHS = 24
# For yearly granularity (if we add such tables): 3 years
LIBRARY_YEARS = 3


def library_month_dates() -> List[date]:
    return months_back(LIBRARY_MONTHS)


def library_daily_dates() -> List[date]:
    return daily_sample_over_months(library_month_dates())


def vary_price(month: date, base: int = 600) -> int:
    """Slight variation by month so trends are visible."""
    return base + (month.month % 5) * 20 + (month.year % 3) * 10


def vary_value(month: date, base: float) -> float:
    return round(base * (1 + (month.month % 6) * 0.02), 2)
