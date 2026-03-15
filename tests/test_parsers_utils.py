"""Tests for parser utilities (safe_decimal, parse_date, etc.)."""
import pytest
from datetime import date
from decimal import Decimal

from parsers.utils import (
    safe_decimal,
    safe_int,
    parse_date,
    parse_month_first,
    normalize_product,
    normalize_location,
    PARSER_VERSION,
    row_meta,
)


def test_safe_decimal():
    assert safe_decimal("1,234.56") == Decimal("1234.56")
    assert safe_decimal("") is None
    assert safe_decimal(None) is None
    assert safe_decimal(42) == Decimal("42")
    assert safe_decimal("  N/A  ") is None


def test_safe_int():
    assert safe_int("1,000") == 1000
    assert safe_int("") is None
    assert safe_int(10) == 10


def test_parse_date():
    assert parse_date("2024-01-15") == date(2024, 1, 15)
    assert parse_date("2024-01") == date(2024, 1, 1)
    assert parse_date("15/01/2024") == date(2024, 1, 15)
    assert parse_date(None) is None
    assert parse_date("") is None


def test_parse_month_first():
    assert parse_month_first("2024-06") == date(2024, 6, 1)
    assert parse_month_first(date(2024, 3, 15)) == date(2024, 3, 1)  # first day of month


def test_normalize_product():
    assert normalize_product("  pms  ") == "PMS"
    assert normalize_product(None) == "Unknown"


def test_normalize_location():
    assert normalize_location("  Lagos  ") == "Lagos"
    assert normalize_location("") == "Unknown"


def test_row_meta():
    m = row_meta("file-123", 1, "table", 0.9)
    assert m["source_file_id"] == "file-123"
    assert m["source_page"] == 1
    assert m["extraction_method"] == "table"
    assert m["confidence_score"] == 0.9
    assert m["parser_version"] == PARSER_VERSION
