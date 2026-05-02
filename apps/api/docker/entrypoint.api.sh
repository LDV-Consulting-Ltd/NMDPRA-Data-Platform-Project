#!/usr/bin/env bash
set -euo pipefail

PGHOST="${PGHOST:-postgres}"
PGPORT="${PGPORT:-5432}"
PGUSER="${POSTGRES_USER:-nmdpra}"
PGDATABASE="${POSTGRES_DB:-nmdpra_data}"

echo "[entrypoint] Waiting for PostgreSQL at ${PGHOST}:${PGPORT}..."
for i in $(seq 1 120); do
  if pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" >/dev/null 2>&1; then
    echo "[entrypoint] PostgreSQL is ready."
    break
  fi
  if [ "$i" -eq 120 ]; then
    echo "[entrypoint] Timeout waiting for PostgreSQL." >&2
    exit 1
  fi
  sleep 1
done

cd /app
echo "[entrypoint] Running Alembic migrations..."
alembic upgrade head

echo "[entrypoint] Starting application..."
exec "$@"
