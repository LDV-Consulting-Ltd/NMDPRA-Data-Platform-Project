"""Tests for Supabase / Postgres URL normalization."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "apps" / "api"
sys.path.insert(0, str(API_DIR))

from app.db_url import normalize_database_url, resolve_database_url  # noqa: E402


def test_normalize_postgres_scheme_to_psycopg2():
    url = normalize_database_url("postgresql://postgres:secret@db.example.supabase.co:5432/postgres")
    assert url.startswith("postgresql+psycopg2://")
    assert "sslmode=require" in url


def test_normalize_postgres_short_scheme():
    url = normalize_database_url("postgres://user:pass@localhost:5432/db")
    assert url.startswith("postgresql+psycopg2://")


def test_resolve_prefers_database_url():
    url = resolve_database_url(
        database_url="postgresql://postgres:x@db.abc.supabase.co:5432/postgres",
        supabase_db_host="ignored.supabase.co",
        supabase_db_password="ignored",
    )
    assert "db.abc.supabase.co" in url
    assert "sslmode=require" in url


def test_resolve_from_supabase_parts():
    url = resolve_database_url(
        supabase_db_host="db.xyz.supabase.co",
        supabase_db_password="p@ss:word",
        supabase_db_user="postgres",
        supabase_db_name="postgres",
        supabase_db_port=5432,
    )
    assert "db.xyz.supabase.co" in url
    assert "sslmode=require" in url
    assert "p%40ss%3Aword" in url


def test_resolve_supabase_db_url_alias():
    url = resolve_database_url(
        supabase_db_url="postgresql://postgres:secret@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
    )
    assert "pooler.supabase.com" in url
    assert "+psycopg2" in url
