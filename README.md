# NMDPRA Data Product Platform (V1)

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
- **Apache Airflow** (Docker) – Orchestration
- **PostgreSQL 15+** – Storage (bronze / silver / gold / meta)
- **FastAPI** – Business + Governance APIs
- **Next.js** (App Router) – Dashboard
- **Docker Compose** – Local dev
- **Parsing**: pdfplumber, camelot/tabula, tesseract (OCR fallback)
- **Diagrams**: Mermaid + CLI export (PNG/SVG)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node 18+ (for local web dev)
- Python 3.11+ (for local API/scripts)

### 1. Clone and configure

```bash
cp .env.example .env
# Edit .env if needed (DB credentials, etc.)
```

### 2. Start services

```bash
make up
# Or: docker compose up -d
```

- **API**: http://localhost:8000 (docs: http://localhost:8000/docs)
- **Dashboard**: http://localhost:3000
- **Airflow**: http://localhost:8080 (admin / admin)

### 3. Run migrations

```bash
make db-upgrade
```

### 4. Pipeline runs

- **On startup**: When you run `make up`, the `pipeline_bootstrap` service runs once after Airflow is healthy and triggers the DAG (conf: `triggered_by: startup`). Then it exits. No fixed schedule.
- **Run when you want**: Use the **Run now** button in the dashboard (Overview or Governance → Coverage). This calls the FastAPI admin endpoint, which triggers the DAG via the Airflow REST API. Set `ADMIN_RUN_TOKEN` in `.env` (and in the `web` service env for the server route); the token is never sent to the browser.
- **Optional**: In Airflow UI (http://localhost:8080), open DAG `nmdpra_end_to_end_dag` → Trigger DAG. Or backfill: `make backfill SOURCE=oilgasdata FROM=2023-01 TO=2026-12`

### 5. Generate diagrams

```bash
make diagrams
# Writes docs/diagrams/*.mmd and optionally PNG/SVG
```

## Project Structure

```
├── apps/
│   ├── api/                 # FastAPI (business + governance)
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   ├── alembic/
│   │   ├── app/ (routers, models, services)
│   └── web/                 # Next.js dashboard
│       ├── app/ (pages, components)
│       └── Dockerfile
├── pipelines/
│   └── airflow/
│       ├── dags/
│       │   └── nmdpra_end_to_end_dag.py
│       └── Dockerfile
├── parsers/                 # Modular PDF parsers
│   ├── oilgasdata_parser.py
│   ├── vesselschedule_parser.py
│   ├── dailytruckout_parser.py
│   └── stockreport_parser.py
├── scripts/
│   ├── generate_diagrams.py
│   └── backfill.py
├── data/                    # Downloaded PDFs (mounted)
├── docs/
│   └── diagrams/            # Mermaid + exported artifacts
├── tests/
├── docker-compose.yml
├── Makefile
└── .env.example
```

## Pipeline (One DAG)

**DAG**: `nmdpra_end_to_end_dag`

1. **Discover** – Scrape NMDPRA pages, extract PDF links → `bronze.file_registry`
2. **Download** – Download new/changed PDFs (hash-based skip)
3. **Parse** – Per-source parsers → bronze tables + rejects
4. **DQ (Bronze)** – Run rules, store `bronze.dq_result`, route bad rows to `bronze.rejects`
5. **Silver** – Normalized model from bronze (dims + facts)
6. **Gold** – Dimensional model (star schemas) from silver
7. **Publish** – Metadata, lineage, diagram generation
8. **Finalize** – Run summary, `ingest_run` / `ingest_run_file`

Supports: **scheduled** (e.g. daily) and **manual** trigger / backfill. Idempotent via URL + content hash.

## APIs

- **Business**: `/v1/reports`, `/v1/highlights`, `/v1/refineries/*`, `/v1/prices/*`, `/v1/vessels/*`, `/v1/archive/*`, etc.
- **Governance**: `/v1/governance/dq/*`, `/v1/governance/metadata/*`, `/v1/governance/lineage/*`, `/v1/governance/audit/*`, `/v1/governance/health/ingestion`

All with pagination, `last_updated`, coverage, and `data_status` (active/archived/paused) where appropriate.

## Dashboard

- **Business**: Overview, Prices, Sufficiency, Refineries, Gas, Vessels, Archive (labeled “Archived”).
- **Governance**: Coverage, DQ, Lineage (Mermaid), Catalog (data dictionary).

UI calls FastAPI only; no direct DB. Coverage + last updated + status banner on dataset pages.

## Data Model

- **Bronze**: Raw extracted tables, file registry, run metadata, rejects, DQ results.
- **Silver**: Normalized entities, conformed dimensions, facts.
- **Gold**: Star schemas (dims + facts) derived strictly from Silver.

## License

Internal / NMDPRA Data Product use.
