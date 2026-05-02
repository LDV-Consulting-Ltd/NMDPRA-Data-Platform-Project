"""
Library seed: enough data to run analysis by time granularity.
- Monthly tables: past 2 years (24 months).
- Daily tables: 2 years coverage with one row per month (24 rows).
"""
from datetime import date
from typing import List

LIBRARY_MONTHS = 24


def months_back(n: int, end: date | None = None) -> List[date]:
    """First-of-month dates for the past n months."""
    end = end or date.today()
    out: List[date] = []
    y, m = end.year, end.month
    for _ in range(n):
        out.append(date(y, m, 1))
        m -= 1
        if m < 1:
            m += 12
            y -= 1
    return out


def daily_sample_over_months(months: List[date], day_of_month: int = 15) -> List[date]:
    """One date per month for 2 years coverage."""
    out: List[date] = []
    for m in months:
        d = min(day_of_month, 28)
        try:
            out.append(date(m.year, m.month, d))
        except ValueError:
            out.append(date(m.year, m.month, 28))
    return out


def library_month_dates() -> List[date]:
    return months_back(LIBRARY_MONTHS)


def library_daily_dates() -> List[date]:
    return daily_sample_over_months(library_month_dates())


def vary_price(month: date, base: int = 600) -> int:
    return base + (month.month % 5) * 20 + (month.year % 3) * 10


def vary_value(month: date, base: float) -> float:
    return round(base * (1 + (month.month % 6) * 0.02), 2)
