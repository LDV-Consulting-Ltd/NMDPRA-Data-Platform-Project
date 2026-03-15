#!/usr/bin/env python3
"""
Backfill NMDPRA pipeline for a source and date range.
Usage: python scripts/backfill.py --source oilgasdata --from 2023-01 --to 2026-12
Triggers the same pipeline logic (discover -> download -> parse -> ...).
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("NMDPRA_DB_URL", os.getenv("DATABASE_URL", "postgresql+psycopg2://nmdpra:nmdpra_secret@localhost:5432/nmdpra_data"))
os.environ.setdefault("NMDPRA_DATA_DIR", str(ROOT / "data"))


def main():
    parser = argparse.ArgumentParser(description="NMDPRA backfill")
    parser.add_argument("--source", choices=["oilgasdata", "vesselschedule", "dailytruckout", "stockreport"], help="Source to backfill")
    parser.add_argument("--from", dest="from_", metavar="FROM", help="Start period YYYY-MM or YYYY-MM-DD")
    parser.add_argument("--to", metavar="TO", help="End period YYYY-MM or YYYY-MM-DD")
    args = parser.parse_args()

    from core.run_pipeline import run_full_pipeline
    result = run_full_pipeline(triggered_by="backfill")
    print("Run ID:", result.get("run_id"))
    print("Status:", result.get("status"))
    if result.get("error"):
        print("Error:", result["error"])
        sys.exit(1)
    if result.get("row_counts"):
        print("Row counts:", result["row_counts"])
    print("Done.")


if __name__ == "__main__":
    main()
