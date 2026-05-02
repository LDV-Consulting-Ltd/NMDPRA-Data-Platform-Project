# NMDPRA Downstream Regulatory Intelligence Platform (V1)

Production-grade, API-first data platform for Nigerian Midstream and Downstream Petroleum Regulatory Authority (NMDPRA) public data, with full governance (DQ, metadata, lineage, audit) and a Next.js dashboard.

## Data Sources

| Source | Page | Status |
|--------|------|--------|
| Oil & Gas Fact Sheets | [OilGasData](https://www.nmdpra.gov.ng/OilGasData) | Active (monthly) |
| Vessel Clearance Schedule | [VesselSchedule](https://www.nmdpra.gov.ng/VesselSchedule) | Active |
| Daily Truckout | [DailyTruckout](https://www.nmdpra.gov.ng/DailyTruckout) | Archived (last 2023) |
| Stock & Days Sufficiency | [StockReport](https://www.nmdpra.gov.ng/StockReport) | Archived (last 2023) |

## Tech Stack

- **Python 3.11+** – Pipelines, parsers, API
- **Orchestration engine** (Apache Airflow in Docker) – runs the automated ingestion workflow internally; operators use **Platform Operations**, not the engine UI, for day-to-day use
- **PostgreSQL 15+** – Storage (bronze / silver / gold / meta)
- **FastAPI** – Business + Governance APIs
- **Next.js** (App Router) – Dashboard
- **Docker Compose** – Local and single-command startup
- **Parsing**: pdfplumber, camelot/tabula, tesseract (OCR fallback)
- **Diagrams**: Mermaid + CLI export (PNG/SVG)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node 18+ (only if you run the web app outside Docker)
- Python 3.11+ (only if you run the API or scripts outside Docker)

### 1. Configure environment

```bash
cp .env.example .env
```

Edit `.env` as needed (database credentials, `ADMIN_RUN_TOKEN` for authorized pipeline runs from the UI, `AIRFLOW_PASSWORD`, etc.). Never commit secrets.

### 2. Start the stack

```bash
make up
```

This builds images (when needed), starts PostgreSQL, applies **Alembic migrations automatically** via the API entrypoint, initializes the orchestration metadata store, starts the orchestration webserver and worker, starts FastAPI and Next.js, unpauses the ingestion workflow, and runs a **one-time bootstrap** ingestion when there is no successful run yet or no downloaded files.

Published ports (see `docker-compose.yml`):

- **Dashboard**: http://localhost:3001 (mapped host port; container listens on 3000)
- **API**: http://localhost:8001 (OpenAPI: `/docs`)
- **Internal orchestration UI** (operators / troubleshooting only): http://localhost:8080

### 3. Use the product

- Open the dashboard URL above. If data is still loading, a short **data readiness** banner explains that ingestion is in progress.
- Authorized operators: open **Operations** in the header or go to **Platform Operations** at `/admin/pipeline` to **Run pipeline**, view status, optional demo seeding, and (optionally) the internal orchestration console link.

No manual migration step is required for normal startup. `make db-upgrade` remains available for maintenance.

### 4. Diagrams (optional)

```bash
make diagrams
```

Writes `docs/diagrams/*.mmd` and optionally PNG/SVG.

## Pipeline behaviour

The automated ingestion workflow runs **only when triggered**: first-time bootstrap (empty or unsuccessful data), or an authorized **Run pipeline** action. There is **no fixed hourly/daily schedule** in the DAG definition (`schedule_interval=None`, `max_active_runs=1`, `catchup=False`).

Steps: discover → download → parse → DQ → silver → gold → publish metadata/lineage → diagrams → finalize.

## Project Structure

```
├── apps/
│   ├── api/                 # FastAPI (business + governance)
│   │   ├── docker/entrypoint.api.sh   # wait Postgres → alembic upgrade → uvicorn
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   ├── alembic/
│   │   └── app/ (routers, models, services)
│   └── web/                 # Next.js dashboard
│       ├── app/ (pages, components)
│       └── Dockerfile
├── pipelines/airflow/
│   ├── dags/nmdpra_end_to_end_dag.py
│   └── Dockerfile
├── core/                    # Pipeline runner + discover (mounted into API & workers)
├── parsers/
├── scripts/
│   ├── bootstrap_pipeline.py   # Startup bootstrap (compose one-shot)
│   ├── generate_diagrams.py
│   └── backfill.py
├── data/
├── docker-compose.yml
├── Makefile
└── .env.example
```

## APIs

- **Business**: `/v1/reports`, `/v1/highlights`, `/v1/refineries/*`, `/v1/prices/*`, `/v1/vessels/*`, `/v1/archive/*`, etc.
- **Governance**: `/v1/governance/dq/*`, `/v1/governance/metadata/*`, `/v1/governance/lineage/*`, `/v1/governance/audit/*`, `/v1/governance/health/ingestion`
- **Dashboard pipeline status (sanitized)**: `/v1/pipeline/status`
- **Admin (token: `X-Admin-Token`)**: `/v1/admin/pipeline/run`, `/status`, `/runs`, `/health`, `/backfill`

The Next.js app proxies privileged routes server-side; **`ADMIN_RUN_TOKEN` is never exposed to the browser**.

## Makefile

| Command | Purpose |
|--------|---------|
| `make up` | Build and start all services |
| `make down` | Stop stack |
| `make logs` | Follow logs |
| `make db-upgrade` | Apply migrations manually (optional; automatic on API start in Docker) |
| `make diagrams` | Generate diagrams |
| `make backfill` | CLI backfill helper |
| `make test` | Run pytest |

## Data Model

- **Bronze**: Raw extracted tables, file registry, run metadata, rejects, DQ results.
- **Silver**: Normalized entities, conformed dimensions, facts.
- **Gold**: Star schemas (dims + facts) derived strictly from Silver.

## License

Internal / NMDPRA Downstream Regulatory Intelligence use.
