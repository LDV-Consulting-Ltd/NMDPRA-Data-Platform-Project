#!/bin/sh
# Create Airflow database (idempotent: ignore error if already exists)
psql -v ON_ERROR_STOP=0 --username "$POSTGRES_USER" --dbname "postgres" -c "CREATE DATABASE airflow;" || true
