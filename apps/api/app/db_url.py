"""
Build / normalize SQLAlchemy database URLs for local Postgres and Supabase.

Priority:
1. DATABASE_URL (or SUPABASE_DB_URL) — paste the Supabase connection string
2. Discrete SUPABASE_DB_* parts if DATABASE_URL is unset
"""
from __future__ import annotations

from typing import Optional
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse, urlunparse


def normalize_database_url(url: str) -> str:
    """Ensure psycopg2 dialect and sslmode=require for hosted Postgres (Supabase)."""
    url = (url or "").strip()
    if not url:
        return url

    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and "+psycopg2" not in url.split("://", 1)[0]:
        url = "postgresql+psycopg2://" + url[len("postgresql://") :]

    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    host = (parsed.hostname or "").lower()
    is_supabase = "supabase.co" in host or "supabase.com" in host
    if is_supabase and "sslmode" not in query:
        query["sslmode"] = "require"
    return urlunparse(parsed._replace(query=urlencode(query)))


def build_database_url_from_supabase(
    *,
    host: str,
    password: str,
    user: str = "postgres",
    dbname: str = "postgres",
    port: int = 5432,
    sslmode: str = "require",
) -> str:
    user = quote_plus((user or "postgres").strip() or "postgres")
    dbname = (dbname or "postgres").strip() or "postgres"
    host = host.strip()
    password = quote_plus(password.strip())
    return normalize_database_url(
        f"postgresql+psycopg2://{user}:{password}@{host}:{int(port)}/{dbname}?sslmode={sslmode}"
    )


def resolve_database_url(
    *,
    database_url: Optional[str] = None,
    supabase_db_url: Optional[str] = None,
    supabase_db_host: Optional[str] = None,
    supabase_db_password: Optional[str] = None,
    supabase_db_user: Optional[str] = None,
    supabase_db_name: Optional[str] = None,
    supabase_db_port: Optional[int] = None,
    supabase_db_sslmode: Optional[str] = None,
    default: str = "postgresql+psycopg2://nmdpra:nmdpra_secret@localhost:5432/nmdpra_data",
) -> str:
    raw = (database_url or "").strip() or (supabase_db_url or "").strip()
    if raw:
        return normalize_database_url(raw)

    host = (supabase_db_host or "").strip()
    password = (supabase_db_password or "").strip()
    if host and password:
        return build_database_url_from_supabase(
            host=host,
            password=password,
            user=(supabase_db_user or "postgres").strip() or "postgres",
            dbname=(supabase_db_name or "postgres").strip() or "postgres",
            port=int(supabase_db_port or 5432),
            sslmode=(supabase_db_sslmode or "require").strip() or "require",
        )

    return normalize_database_url(default)
