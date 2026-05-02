"""Optional: start Airflow stack via docker compose from the API container (requires Docker socket + ENABLE_AIRFLOW_DOCKER_START)."""
import os
import subprocess
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

router = APIRouter()

DEFAULT_SERVICES = "postgres airflow-webserver airflow-scheduler"
MANUAL_COMMAND = f"docker compose up -d {DEFAULT_SERVICES}"


def _require_admin(x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    token = os.environ.get("ADMIN_RUN_TOKEN", "")
    if not token or x_admin_token != token:
        raise HTTPException(401, "Unauthorized")


def _docker_start_enabled() -> bool:
    return os.getenv("ENABLE_AIRFLOW_DOCKER_START", "").strip().lower() in ("1", "true", "yes", "on")


@router.post("/start-airflow")
def start_airflow(_: None = Depends(_require_admin)):
    """
    Start postgres (if needed), Airflow webserver and scheduler.
    When ENABLE_AIRFLOW_DOCKER_START is not set, returns instructions + manual command (no Docker run).
    """
    if not _docker_start_enabled():
        return {
            "started": False,
            "mode": "manual",
            "message": "API is not allowed to run Docker on this deployment. Run the command below in your project root.",
            "command": MANUAL_COMMAND,
            "airflow_url": "http://localhost:8080",
        }
    cwd = os.getenv("COMPOSE_PROJECT_DIR", "/workspace").strip() or "/workspace"
    compose_file = os.getenv("COMPOSE_FILE", "docker-compose.yml").strip() or "docker-compose.yml"
    if not os.path.isdir(cwd):
        raise HTTPException(
            503,
            detail=f"COMPOSE_PROJECT_DIR is not a directory: {cwd}. Mount the repo root at /workspace in the API service.",
        )
    compose_path = os.path.join(cwd, compose_file)
    if not os.path.isfile(compose_path):
        raise HTTPException(
            503,
            detail=f"Compose file not found: {compose_path}",
        )
    services = os.getenv("AIRFLOW_COMPOSE_SERVICES", DEFAULT_SERVICES).strip().split()
    if not services:
        services = DEFAULT_SERVICES.split()
    cmd = ["docker", "compose", "-f", compose_file, "up", "-d", *services]
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except FileNotFoundError:
        raise HTTPException(503, detail="docker CLI not found in the API container.")
    except subprocess.TimeoutExpired:
        raise HTTPException(504, detail="docker compose timed out after 300s.")
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip() or "docker compose failed"
        raise HTTPException(500, detail=err[:4000])
    return {
        "started": True,
        "mode": "docker",
        "message": "Airflow webserver and scheduler were started (and postgres ensured).",
        "stdout": (proc.stdout or "").strip()[-8000:],
        "airflow_url": "http://localhost:8080",
        "command": MANUAL_COMMAND,
    }
