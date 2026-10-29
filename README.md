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

### Vercel Services (multi-service project)

Root `vercel.json` deploys **two services** in one project:

| Service | Root | Role |
|---------|------|------|
| `web` | `apps/web` | Next.js dashboard (public catch-all) |
| `api` | `apps/api` | FastAPI (public on selected paths; also bound internally) |

**Public paths → `api`:** `/v1/*`, `/api/v1/tanna/*`, `/health`, `/openapi.json`, `/docs`, `/redoc`.  
**Everything else → `web`:** including Next.js BFF routes under `/api/pipeline/*`, `/api/seed-demo`, `/api/data-layers/*` (do **not** rewrite all of `/api/*` to FastAPI).

**Binding:** `web` → `api` injects `API_URL` at runtime for server-side fetches. Do not set `API_URL` yourself in Vercel when using bindings. Browser calls use same-origin `/v1/...` when `NEXT_PUBLIC_API_URL` is unset.

```bash
vercel dev    # runs both services; injects bindings
```

**Not on Vercel:** Postgres, Airflow, MinIO, and ingestion workers remain external (Docker Compose / managed DB). Configure `DATABASE_URL` (and related secrets) on the `api` service.

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

- **Product manifest (PetroGrid v0.1)**: `GET /v1/product/manifest` — formal capability surface for internal services and future Tanna connector integration (implemented vs unsupported features, data layers, API groups, limitations). Public; no auth.
- **Data product registry (PetroGrid v0.1)**: `GET /v1/product/data-products` — formal catalog of real PetroGrid data products backed by existing APIs, bronze tables, or gold tables (per the PetroGrid → Tanna mapping report). Use this before Tanna connector work to see what exists today.

  **Groups**
  - *API data products* — reports, coverage, highlights, refineries, consumption, fuel prices, gas infrastructure, charts, vessels, archive, data layers (each maps to a live `/v1/*` route and underlying `bronze.*` table).
  - *Bronze data products* — tables from `001_initial_schemas.py` (ingest metadata, domain extracts, DQ).
  - *Gold data products* — warehouse dims/facts from migration; introspection only (no dedicated read APIs yet).

  **Per-product fields**: `product_id`, `product_name`, `description`, `domain`, `source_layer`, `backing_api`, `backing_table`, `freshness_source`, `quality_source`, `status`, `limitations`, plus flags `api_backed`, `table_backed`, `gold_backed`, `tanna_sync_ready`. Silver is listed under `excluded_layers` only (schema exists; pipeline does not persist silver). Public; no auth.

- **Signals (PetroGrid v0.1)**: `GET /v1/product/signals` — rule-based attention indicators computed at request time from existing operational, governance, and API evidence.

  **What signals are**: early indicators that something requires attention — e.g. pipeline failure, data not ready, DQ failures, empty coverage, or missing business API backing data. Signals answer *“What requires attention?”* or *“What changed, degraded, failed, or crossed a threshold?”*

  **What signals are not**: patterns, illuminations, decision products, recommendations, market intelligence, ML/AI forecasts, or pricing anomaly engines. Those are not implemented in v0.1.

  **Supported signal types**: `pipeline_status_signal`, `ingestion_health_signal`, `data_readiness_signal`, `dq_failure_signal`, `source_coverage_signal`, `api_coverage_signal`, `data_layer_availability_signal`, `fuel_price_availability_signal`, `refinery_status_availability_signal`, `vessel_clearance_availability_signal`, `archive_availability_signal`.

  **Evidence sources** (read-only): `/health`, `/v1/pipeline/status`, `/v1/governance/health/ingestion`, `/v1/governance/dq/results` (via DQ counts on latest run), `/v1/coverage`, `/v1/reports`, `/v1/data-layers/tables`, `/v1/refineries/status`, `/v1/prices/fuel`, `/v1/vessels/clearance`, `/v1/archive/*` backing tables. Unavailable sources are skipped with metadata warnings; the endpoint does not crash.

  **Rules**: transparent configuration in `apps/api/app/product_signals/rules.py` (e.g. `data_ready_false`, `pipeline_status_failed`, `dq_failures_count_gt_0`, `coverage_empty`, `gold_layer_empty`). Every emitted signal includes structured `evidence`.

  **Limitations**: no signal persistence or acknowledgement workflow yet; all signals return `status: new`. No database writes; no ingestion or backfill side effects.

- **Patterns (PetroGrid v0.1)**: `GET /v1/product/patterns` — rule-based clustered structures derived from PetroGrid Signals v0.1.

  **What patterns are**: repeated or clustered signal structures — e.g. pipeline + data-readiness + coverage signals co-occurring, or multiple business dataset availability gaps clustering together. Patterns answer *“What keeps happening, recurring, clustering, or emerging across signals?”*

  **How patterns differ from signals**: signals flag individual attention items; patterns group co-occurring signals that share signal types, data products, or operational domains. Patterns are not illuminations or decision products.

  **Supported pattern types**: `recurring_pipeline_issue_pattern`, `recurring_ingestion_health_pattern`, `repeated_data_readiness_issue_pattern`, `repeated_dq_failure_pattern`, `recurring_coverage_gap_pattern`, `recurring_api_availability_gap_pattern`, `recurring_data_layer_availability_gap_pattern`, `recurring_business_dataset_gap_pattern`.

  **Primary input**: `GET /v1/product/signals` (reused internally). Every pattern includes structured `evidence` with `rule`, `threshold`, `observed_signal_count`, `source_signal_ids`, and `signal_types`.

  **Rules**: transparent configuration in `apps/api/app/product_patterns/rules.py` (e.g. `minimum_related_signals`, `minimum_signal_types_for_cluster`, `repeated_source_gap_threshold`). Empty signals produce empty patterns.

  **Limitations**: v0.1 clusters co-occurring signals at request time only (not historical recurrence across runs). No pattern persistence; all patterns return `status: new`. No database writes; no ingestion or backfill side effects.

- **Illuminations (PetroGrid v0.1)**: `GET /v1/product/illuminations` — rule-based operational and business context derived from Signals and Patterns v0.1.

  **What illuminations are**: conservative contextual interpretation of what clustered signals and patterns may mean for operations — e.g. data readiness gaps may affect dashboard reliability, or coverage gaps may affect governance completeness. Illuminations answer *“What does this mean in business or operational context?”*

  **How illuminations differ from signals and patterns**: signals flag individual attention items; patterns cluster co-occurring signals; illuminations add cautious operational context using conservative language (`may indicate`, `suggests`, `could affect`, `requires review`, `appears to`). Illuminations are not decisions, recommendations, AI narratives, or forecasts.

  **Supported illumination types**: `data_readiness_illumination`, `ingestion_health_illumination`, `dq_reliability_illumination`, `coverage_gap_illumination`, `api_availability_illumination`, `data_layer_availability_illumination`, `business_dataset_gap_illumination`.

  **Primary inputs**: `GET /v1/product/signals` and patterns evaluated from those signals (reused internally). Every illumination includes `evidence` with `source_pattern_ids`, `source_signal_ids`, `rule`, `threshold`, and `observed_value`.

  **Rules**: transparent configuration in `apps/api/app/product_illuminations/rules.py`. Empty signals and patterns produce empty illuminations.

  **Limitations**: v0.1 is computed at request time with `status: new` only; no persistence or acknowledgement workflow. No price anomaly, supply shortage, market, or regulatory compliance intelligence. No database writes; no ingestion or backfill side effects.

- **Decision Products (PetroGrid v0.1)**: `GET /v1/product/decision-products` — rule-based decision-support objects derived from signals, patterns, and illuminations.

  **What decision products are**: structured objects that connect evidence, operational context, and human decision areas — e.g. a coverage gap review that supports assessment of whether source download workflows need attention. Decision products answer *“What decision does this support?”*

  **How they differ from illuminations**: illuminations explain operational meaning; decision products frame a specific human review area with owner role, supported decision scope, and linked evidence. They are not automated decisions, approvals, or AI recommendations.

  **Supported decision types**: `data_readiness_review`, `ingestion_health_review`, `dq_remediation_review`, `coverage_gap_review`, `api_availability_review`, `data_layer_readiness_review`, `business_dataset_readiness_review`.

  **Placeholder semantics**: `placeholder: false` when derived from an existing illumination; `placeholder: true` for shells built only from signals/patterns when illumination context is unavailable. All products return `decision_status: draft`.

  **Language**: review-oriented only (`supports review of`, `helps assess`, `provides evidence for`, `may inform`, `requires human review`). No automated approval or enforcement language.

  **Rules**: transparent configuration in `apps/api/app/product_decisions/rules.py`. Empty upstream inputs produce empty decision products.

  **Limitations**: no approval workflows, task management, persistence, pricing/supply/regulatory/investment decisions, or forecasting. No database writes; no ingestion or backfill side effects.

- **Relationships (PetroGrid v0.1)**: `GET /v1/product/relationships` — evidence-backed links between PetroGrid objects for traceability, lineage, and Tanna connector readiness. Manifest capability: `relationship_surface`.

  **What relationships are**: formal connections answering *“How are those objects connected?”* — e.g. a data product served by an API endpoint, an API endpoint reading a bronze table, a gold fact referencing a dimension via migration FK, or a bronze extract sourced from `bronze.file_registry`.

  **How relationships differ from signals, patterns, illuminations, and decision products**: relationships describe structural links with explicit evidence (FKs, registry fields, pipeline mappings, lineage records). Signals, patterns, illuminations, and decision products are rule-evaluated interpretations of operational state — they do not assert graph topology.

  **Evidence sources** (read-only): gold foreign keys and `source_file_id` references from `001_initial_schemas.py`, data product registry `backing_api` / `backing_table` mappings, entities v0.1 (`GET /v1/product/entities`), `run_silver_gold` gold←bronze mappings, governance lineage edge records (when present), and manifest knowledge assets. No inferred or causal relationships.

  **Supported relationship types**: `contains`, `references`, `sourced_from`, `derived_from`, `loaded_into`, `produces`, `consumed_by`, `documented_by`, `represented_by`, `belongs_to`.

  **Confidence bands**: foreign keys 0.9–1.0; lineage edges 0.8–0.9; `source_file_id` references 0.7–0.8; documentation-backed links 0.6–0.7. Relationships below 0.6 confidence are not emitted.

  **Categories** (response `groups`): data product→API endpoint, API endpoint→bronze table, gold fact→gold dimension, source file→bronze table, bronze table→gold table, report→source file, knowledge asset→data product, entity→data product, lineage node→lineage node.

  **Limitations**: computed at request time; no relationship persistence or writes. When `meta.lineage_edge` is empty, the `lineage_node_to_lineage_node` group is empty with an explicit limitation note. No graph database (Neo4j) yet — relationships are a read-only product surface over existing metadata, not a separate graph store.

- **Entities (PetroGrid v0.1)**: `GET /v1/product/entities` — evidence-backed catalog of real PetroGrid business objects.

  **What entities are**: formal representations of what PetroGrid knows exists — products, locations, facilities, reports, source files, ingestion runs, data layer tables, API products, refineries, vessels, gas infrastructure items, and fuel price locations.

  **Evidence sources**: migration schema (`001_initial_schemas.py`), data product registry, Pydantic schemas (`apps/api/app/schemas.py`), and safe read-only instance queries (capped per request). Each entity includes `evidence`, `confidence`, `attributes`, and `limitations`.

  **Response shape**: one type summary per allowed entity group (`status: summary`) plus static API product and data-layer table entities, with optional DB-backed instances when tables are queryable.

  **Limitations**: no invented entities, no persistence, no schema changes. Instance enumeration is capped; empty tables return summaries only with metadata warnings.

- **Knowledge Assets (PetroGrid v0.1)**: `GET /v1/product/knowledge-assets` — catalog of documentation and explanatory artifacts that help users understand PetroGrid.

  **What knowledge assets are**: read-only references to real repository documents, OpenAPI, Mermaid diagram exports, and governance metadata endpoints — not ingested content, AI summaries, or vector indexes.

  **Supported asset types**: `technical_documentation`, `business_article`, `product_analysis`, `case_study`, `openapi_spec`, `mermaid_diagram`, `data_dictionary`, `lineage_metadata`, `data_layer_metadata`, `architecture_reference`.

  **Evidence sources**: `README.md`, `PRODUCT_ARTICLE_BUSINESS.md`, `PRODUCT_ANALYSIS.md`, `CASE_STUDY_NMDPRA.md`, `/openapi.json`, `apps/web/lib/diagrams.ts`, `/v1/governance/metadata/dictionary`, `/v1/governance/lineage/*`, `/v1/data-layers/tables`. Missing files are omitted with metadata warnings; generated PNG/SVG outputs are not claimed unless present.

  **Limitations**: short read-only previews only (no document rewriting); no document ingestion, vector search, or AI summarization.

- **Tanna Connector (PetroGrid v0.1)**: protected `/api/v1/tanna/*` endpoints for Tanna registration, health checks, and object sync. PetroGrid remains standalone; Tanna must not access PetroGrid databases directly.

  **Purpose**: standardized connector surface so Tanna can register PetroGrid, test connectivity, inspect maturity, and sync objects using stable `external_id` values.

  **Authentication**: `Authorization: Bearer <TANNA_CONNECTOR_TOKEN>`. Missing token → `401`. Invalid token → `403`. Set `TANNA_CONNECTOR_TOKEN` in the API environment (never log token values).

  **Endpoints**:

  | Connector endpoint | PetroGrid source |
  |--------------------|------------------|
  | `GET /api/v1/tanna/manifest` | `/v1/product/manifest` |
  | `GET /api/v1/tanna/health` | `/health`, `/v1/pipeline/status`, `/v1/governance/health/ingestion`, optional `/v1/admin/pipeline/health` |
  | `GET /api/v1/tanna/status` | maturity matrix across all connector surfaces |
  | `GET /api/v1/tanna/data-products` | `/v1/product/data-products` |
  | `GET /api/v1/tanna/entities` | `/v1/product/entities` |
  | `GET /api/v1/tanna/relationships` | `/v1/product/relationships` |
  | `GET /api/v1/tanna/signals` | `/v1/product/signals` |
  | `GET /api/v1/tanna/patterns` | `/v1/product/patterns` |
  | `GET /api/v1/tanna/illuminations` | `/v1/product/illuminations` |
  | `GET /api/v1/tanna/decision-products` | `/v1/product/decision-products` |
  | `GET /api/v1/tanna/knowledge-assets` | `/v1/product/knowledge-assets` |

  **Response envelope**: every connector endpoint returns `module_id`, `module_name`, `object_type`, `implementation_status`, `items`, and `metadata` (`sync_ready`, `sync_notes`, `external_id_strategy`, `duplicate_handling_notes`, `generated_at`).

  **External IDs**: `petrogrid:{object_type}:{stable_identifier}` (e.g. `petrogrid:data_product:api_reports`, `petrogrid:entity:refinery:warri`).

  **Maturity matrix** (`GET /api/v1/tanna/status`): reports `connector_version`, per-endpoint `implementation_status`, `sync_ready`, object counts, and classified `implemented_objects`, `partial_objects`, `placeholder_objects`, `not_implemented_objects`, `sync_ready_objects`, `sync_blocked_objects`.

  **Sync readiness**: `implemented` endpoints → `sync_ready: true`; `partial` → `sync_ready: true` only when objects have stable `external_id` values and limitations are documented; `placeholder` / `not_implemented` → `sync_ready: false`.

  **How Tanna should register PetroGrid**: (1) configure `TANNA_CONNECTOR_TOKEN` on both sides, (2) call `/api/v1/tanna/status` to verify maturity, (3) call `/api/v1/tanna/manifest` for capabilities, (4) sync objects from data-products, entities, relationships, signals, patterns, illuminations, decision-products, and knowledge-assets using `external_id` as the upsert key.

  **Known limitations**: no Tanna Core sync engine in this repo; connector is read-only and maps existing product surfaces; health may be `partial` when admin pipeline token is unset; intelligence objects may be empty when upstream evidence is absent; no graph database or direct DB access for Tanna.

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
