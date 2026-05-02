#!/usr/bin/env python3
"""
One-shot startup bootstrap: if no successful ingestion exists yet, trigger the end-to-end pipeline.
Used by docker-compose service pipeline-bootstrap (restart: no).
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request


def get_json(url: str, timeout: int = 60) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def post_json(url: str, body: dict, auth: tuple[str, str] | None, timeout: int = 120) -> tuple[int, dict]:
    data = json.dumps(body).encode()
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    req = urllib.request.Request(url, data=data, method="POST", headers=headers)
    if auth:
        import base64

        token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode() if e.fp else "{}"
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"detail": raw}


def main() -> int:
    api_base = os.environ.get("API_URL", "http://api:8000").rstrip("/")
    airflow_base = os.environ.get("AIRFLOW_API_BASE", "http://airflow-webserver:8080/api/v1").rstrip("/")
    user = os.environ.get("AIRFLOW_USERNAME", "admin")
    pw = os.environ.get("AIRFLOW_PASSWORD", "admin")

    print("[bootstrap] Waiting for API health...")
    for i in range(120):
        try:
            get_json(f"{api_base}/health", timeout=5)
            print("[bootstrap] API is up.")
            break
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
            pass
        if i == 119:
            print("[bootstrap] ERROR: API never became healthy.", file=sys.stderr)
            return 1
        time.sleep(2)

    af_health = os.environ.get("AIRFLOW_HEALTH_URL", "http://airflow-webserver:8080/health")
    print("[bootstrap] Waiting for orchestration health...")
    for i in range(120):
        try:
            req = urllib.request.Request(af_health)
            with urllib.request.urlopen(req, timeout=5):
                pass
            print("[bootstrap] Orchestration endpoint responded.")
            break
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
            pass
        if i == 119:
            print("[bootstrap] ERROR: Orchestration never became reachable.", file=sys.stderr)
            return 1
        time.sleep(2)

    try:
        ing = get_json(f"{api_base}/v1/governance/health/ingestion")
        data = ing.get("data") or {}
    except Exception as e:
        print(f"[bootstrap] WARNING: could not read ingestion health: {e}")
        data = {}

    has_success = bool(data.get("has_successful_run"))
    ingested = int(data.get("ingested_file_count") or 0)
    print(f"[bootstrap] has_successful_run={has_success} ingested_file_count={ingested}")

    if has_success and ingested > 0:
        print("[bootstrap] Skip: existing successful run and ingested files present.")
        return 0

    print("[bootstrap] Triggering pipeline run (startup / initial_bootstrap)...")
    code, resp = post_json(
        f"{airflow_base}/dags/nmdpra_end_to_end_dag/dagRuns",
        {"conf": {"triggered_by": "startup", "reason": "initial_bootstrap"}},
        auth=(user, pw),
    )
    if code >= 300:
        print(f"[bootstrap] WARNING: trigger returned {code}: {resp}", file=sys.stderr)
        return 0 if code == 409 else 1
    print("[bootstrap] Trigger accepted:", resp.get("dag_run_id") or resp.get("dag_run", {}).get("dag_run_id"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
