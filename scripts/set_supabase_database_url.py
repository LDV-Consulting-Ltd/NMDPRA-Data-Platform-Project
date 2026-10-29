"""
Apply a rotated Supabase DB password to local .env and Vercel project env.

Usage (PowerShell):
  $env:SUPABASE_DB_PASSWORD = 'new-password-from-dashboard'
  python scripts/set_supabase_database_url.py

Optional:
  $env:SUPABASE_ACCESS_TOKEN = 'sbp_...'   # rotates via Management API first
  $env:NEW_DB_PASSWORD = '...'            # password to set via API (else generates one)
"""
from __future__ import annotations

import json
import os
import secrets
import string
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
SECRETS_DIR = ROOT / ".secrets"

PROJECT_REF = "cbmwzdsdnanbescciebj"
POOLER_HOST = "aws-0-us-east-1.pooler.supabase.com"
POOLER_PORT = 5432
DB_NAME = "postgres"
DB_USER = f"postgres.{PROJECT_REF}"
VERCEL_PROJECT = "nmdpra-data-platform"
VERCEL_SCOPE = "ladvconsulting-2075s-projects"


def _generate_password() -> str:
    alphabet = string.ascii_letters + string.digits + "-_"
    return "".join(secrets.choice(alphabet) for _ in range(40))


def build_url(password: str) -> str:
    return (
        f"postgresql+psycopg2://{quote_plus(DB_USER)}:{quote_plus(password)}"
        f"@{POOLER_HOST}:{POOLER_PORT}/{DB_NAME}?sslmode=require"
    )


def rotate_via_management_api(password: str, token: str) -> None:
    req = urllib.request.Request(
        f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/password",
        data=json.dumps({"password": password}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="PATCH",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            print(f"Management API rotate OK ({resp.status}): {body[:200]}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Management API rotate failed ({exc.code}): {detail}") from exc


def update_dotenv(url: str) -> None:
    lines: list[str] = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith("DATABASE_URL="):
            out.append(f"DATABASE_URL={url}")
            replaced = True
        elif line.startswith("SUPABASE_DB_PASSWORD="):
            continue
        else:
            out.append(line)
    if not replaced:
        out.append(f"DATABASE_URL={url}")
    ENV_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Updated {ENV_PATH}")


def write_secret_file(url: str) -> Path:
    SECRETS_DIR.mkdir(exist_ok=True)
    path = SECRETS_DIR / "supabase_database_url.txt"
    path.write_text(url + "\n", encoding="utf-8")
    (SECRETS_DIR / "README.txt").write_text(
        "Local-only. Never commit. Used for Vercel env sync.\n",
        encoding="utf-8",
    )
    return path


def verify_connection(url: str) -> None:
    from sqlalchemy import create_engine, text

    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("select 1"))
    print("DB connection verified")


def _npx_cmd() -> list[str]:
    # Windows: subprocess cannot resolve npx.ps1 without shell=True.
    if os.name == "nt":
        return ["cmd", "/c", "npx", "--yes"]
    return ["npx", "--yes"]


def set_vercel_env(url: str) -> None:
    npx = _npx_cmd()
    # Remove existing DATABASE_URL for production/preview if present, then add.
    for env_target in ("production", "preview"):
        remove = subprocess.run(
            [
                *npx,
                "vercel",
                "env",
                "rm",
                "DATABASE_URL",
                env_target,
                "--yes",
                "--scope",
                VERCEL_SCOPE,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        # Ignore missing var.
        print(remove.stdout or remove.stderr)

        add = subprocess.run(
            [
                *npx,
                "vercel",
                "env",
                "add",
                "DATABASE_URL",
                env_target,
                "--scope",
                VERCEL_SCOPE,
            ],
            cwd=ROOT,
            input=url + "\n",
            capture_output=True,
            text=True,
        )
        if add.returncode != 0:
            raise SystemExit(
                f"vercel env add failed for {env_target}:\n{add.stdout}\n{add.stderr}"
            )
        print(f"Set Vercel DATABASE_URL ({env_target})")


def main() -> int:
    token = (os.getenv("SUPABASE_ACCESS_TOKEN") or "").strip()
    password = (
        os.getenv("SUPABASE_DB_PASSWORD")
        or os.getenv("NEW_DB_PASSWORD")
        or ""
    ).strip()

    if token:
        if not password:
            password = _generate_password()
            print("Generated new password for Management API rotate")
        rotate_via_management_api(password, token)
    elif not password:
        print(
            "Need either:\n"
            "  SUPABASE_ACCESS_TOKEN (+ optional NEW_DB_PASSWORD), or\n"
            "  SUPABASE_DB_PASSWORD from Dashboard → Database → Reset database password\n"
            f"Open: https://supabase.com/dashboard/project/{PROJECT_REF}/database/settings",
            file=sys.stderr,
        )
        return 2

    url = build_url(password)
    update_dotenv(url)
    secret_path = write_secret_file(url)
    print(f"Wrote {secret_path}")

    try:
        verify_connection(url)
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: could not verify connection yet: {exc}", file=sys.stderr)
        print("If you just rotated, wait ~30s and re-run with the same password.", file=sys.stderr)
        return 3

    set_vercel_env(url)
    print("Done. Password is only in local .env / .secrets and Vercel project env.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
