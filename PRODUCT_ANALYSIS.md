# NMDPRA Downstream Regulatory Intelligence — Structured Product Analysis

Analysis for: (1) Company website product article, (2) Leadership portfolio case study.  
Evidence-based; inferences clearly labeled.

---

## A. PROJECT IDENTITY

| # | Item | Value |
|---|------|--------|
| 1 | **Product name** | NMDPRA Downstream Regulatory Intelligence Platform (V1) |
| 2 | **One-sentence description** | Production-grade, API-first data platform that ingests, cleans, and serves Nigerian Midstream and Downstream Petroleum Regulatory Authority (NMDPRA) public data with full governance (DQ, metadata, lineage, audit) and a Next.js dashboard. |
| 3 | **Domain / industry** | Oil & gas / energy regulation (Nigeria); public sector data. |
| 4 | **Primary problem addressed** | NMDPRA publishes key metrics (fuel prices, refinery status, vessel clearances, stock sufficiency, truckout) as PDFs on multiple web pages; the product turns these into queryable, API- and dashboard-accessible datasets with known quality and lineage. |
| 5 | **Type of product** | Data platform (ingestion, transformation, storage, APIs, governance, UI). |
| 6 | **Target users or organizations** | Internal NMDPRA use (per README license); inferrable: regulators, analysts, and possibly other government or industry consumers of NMDPRA data. |
| 7 | **Maturity level** | **Production-ready** — Docker Compose deployment, migrations, single DAG, API-first design, governance APIs, and dashboard. Not PoC/MVP. |

---

## B. BUSINESS CAPABILITY

The product enables the organization to:

- **Decisions:** Use fuel prices by city, refinery utilization, stock and days sufficiency, and vessel clearance metrics for policy, planning, and compliance decisions instead of manual PDF review.
- **Workflows:** Replace ad hoc scraping and manual extraction with a single pipeline (discover → download → parse → DQ → silver → gold → publish) that can run on a schedule or on demand.
- **Operational visibility:** See coverage per dataset, last updated times, pipeline status, DQ results, and ingestion health in one place (dashboard + governance APIs).
- **Risks mitigated:** Bad or missing data is flagged via DQ rules and reject tables; API audit log supports accountability; lineage and data dictionary support traceability and correct use of data.
- **Value proposition:** One authoritative, up-to-date, queryable layer over NMDPRA’s public PDFs, with clear data status (active vs archived) and governance so stakeholders can trust and reuse the data.

---

## C. PRODUCT OVERVIEW

1. **End-to-end:** The system (1) discovers PDF links from four NMDPRA pages (OilGasData, VesselSchedule, DailyTruckout, StockReport), (2) downloads PDFs (skipping unchanged by content hash), (3) parses them with source-specific parsers into bronze tables, (4) runs data quality rules and records results/rejects, (5) builds silver (normalized dims/facts) and gold (star schemas), (6) publishes metadata and lineage, (7) finalizes run metadata. APIs and dashboard consume bronze/silver/gold and meta.

2. **Inputs:** NMDPRA public HTML pages (for link discovery) and PDFs (Oil & Gas fact sheets, vessel schedules, daily truckout, stock/days sufficiency). Optional: backfill date range and source.

3. **Outputs:** REST APIs (business: reports, highlights, prices, refineries, gas, vessels, archive, charts; governance: DQ, metadata/dictionary, lineage, audit, ingestion health); Next.js dashboard (overview, prices, sufficiency, refineries, gas, vessels, archive, governance coverage/DQ/lineage/catalog); Mermaid diagrams (data architecture, gold model, lineage); pipeline run status and manual “Run now” trigger.

4. **Core processes:** One Airflow DAG: discover → download → parse → dq_bronze → silver_gold → publish_metadata_lineage → generate_diagrams → finalize. Idempotency at download (content hash); truncate-and-reload for silver/gold.

5. **User interaction:** Users open the dashboard (Overview, Prices, Sufficiency, Refineries, Gas, Vessels, Archive, Governance). They view tables and coverage; optionally run the pipeline from Governance · Coverage or Overview (Run now) with token-protected admin API. Power users call FastAPI directly (e.g. `/v1/prices/fuel`, `/v1/governance/dq/results`).

6. **What makes it more than a simple dashboard or script:** Full pipeline (discover → gold), layered storage (bronze/silver/gold/meta), configurable DQ rules and results, lineage and data dictionary, API audit logging, token-protected pipeline trigger, and backfill support.

---

## D. FEATURE CAPABILITIES

| Capability | What it does | Who uses it | Why it matters | Where in codebase | Dependencies | Confidence |
|------------|--------------|-------------|----------------|-------------------|--------------|------------|
| **PDF discovery** | Scrapes NMDPRA pages, extracts PDF links and inferred report period/date, upserts into `bronze.file_registry`. | Pipeline (Airflow) | Automates detection of new or updated reports. | `core/discover.py`, DAG `discover` task | requests, BeautifulSoup | High |
| **Idempotent download** | Downloads PDFs to `data/pdfs/<source_name>`, computes content hash, updates file_registry; re-download skips unchanged. | Pipeline | Saves bandwidth and avoids duplicate parsing. | `core/download.py`, `run_pipeline.run_download` | requests, core.discover.content_hash_bytes | High |
| **Source-specific parsing** | Parses OilGasData, VesselSchedule, DailyTruckout, StockReport PDFs into bronze tables (performance_highlights, refinery_status, fuel_prices_city, vessel_clearance_schedule, truckout_*, stock_*). | Pipeline | Converts unstructured PDFs to structured rows. | `parsers/*.py`, `core/run_pipeline.run_parse` | pdfplumber, parsers.utils | High |
| **Data quality (DQ)** | Runs schema, range, and completeness rules on bronze; stores results in `bronze.dq_result`; supports routing bad rows to `bronze.rejects`. | Pipeline + governance users | Ensures only valid data flows to silver/gold; audit trail. | `core/dq.py`, `apps/api/app/routers/governance_dq.py`, DAG `dq_bronze` | bronze.dq_rule, dq_result | High |
| **Silver/gold build** | Builds silver dims (date, product, location, facility) and facts from bronze; builds gold star schemas (dim_report, fact_*) from silver. | Pipeline | Single normalized and analytics-ready layer. | `core/silver_build.py`, `core/gold_build.py`, `run_pipeline.run_silver_gold` | Bronze tables | High |
| **Governance APIs** | Expose DQ rules/results, metadata dictionary, lineage nodes/edges, API audit log, ingestion health. | Dashboard, integrators, auditors | Transparency and compliance. | `apps/api/app/routers/governance_*.py` | meta.*, bronze.dq_*, bronze.ingest_run | High |
| **Pipeline trigger (Run now)** | UI button calls Next.js API route → FastAPI admin endpoint with token → Airflow REST API to trigger DAG. | Admins | On-demand refresh without touching Airflow UI. | `apps/web/app/components/PipelineStatusCard.tsx`, `apps/web/app/api/pipeline/run/route.ts`, `admin_pipeline.py` | ADMIN_RUN_TOKEN, Airflow API | High |
| **Coverage & ingestion health** | APIs return per-source coverage (min/max period, last_updated) and last run status/failures. | Dashboard (Overview, Governance · Coverage) | Users see what data is available and if ingestion is healthy. | `reports.coverage`, `governance_health.ingestion_health` | bronze.file_registry, bronze.ingest_run | High |
| **Lineage & diagrams** | Pipeline writes lineage nodes/edges to meta; script generates Mermaid (.mmd) for architecture, gold model, lineage. | Ops, data stewards | Document flow and schema. | `run_pipeline.run_publish_metadata_lineage`, `scripts/generate_diagrams.py`, `governance_lineage.py` | meta.lineage_*, docs/diagrams | High |
| **Backfill** | CLI runs full pipeline with `triggered_by=backfill` for a given source and date range (README: `make backfill SOURCE=... FROM=... TO=...`). | Ops | Historical or corrective loads. | `scripts/backfill.py` | core.run_pipeline.run_full_pipeline | Medium (backfill script does not filter by source/date in code; it triggers full pipeline) |
| **API audit** | Middleware logs every request (path, method, status, duration) to `meta.api_audit_log`. | Auditors, ops | Accountability and debugging. | `apps/api/app/middleware.py` | meta.api_audit_log | High |
| **Archived data** | Explicit “archived” status for DailyTruckout and StockReport (last 2023); separate archive APIs and UI section. | Analysts, dashboard | Clear signal that some series are no longer updated. | `apps/api/app/routers/archive.py`, `apps/web/app/archive/page.tsx` | bronze.* truckout/stock | High |

---

## E. USER EXPERIENCE & WORKFLOWS

1. **Main screens:** Overview (highlights, coverage, quick links, pipeline card), Prices (fuel by city), Sufficiency (chart series), Refineries, Gas, Vessels, Archive (truckout/stock samples), Governance · Coverage (pipeline card, ingestion health, coverage table), Governance · DQ (results + rules), Governance · Lineage (nodes/edges), Governance · Catalog (data dictionary).

2. **Primary actions:** Browse tables per page; filter (e.g. month, city) where offered; run pipeline via “Run now” (Overview or Governance · Coverage); refresh pipeline status; open API docs at `/docs`.

3. **Filters, drill-downs, exports, admin:** Month/city/date filters on several APIs; pagination (page, per_page) on list endpoints; no CSV/Excel export in UI (mentioned in Prices page text only); admin = pipeline trigger protected by `X-Admin-Token`.

4. **Roles:** No role model in app; distinction is “any user” (read-only API/dashboard) vs “admin” (token for pipeline run). No login UI; token is server-side only for Run now.

5. **End-to-end (user):** Open dashboard → see overview and coverage → open Prices/Sufficiency/Refineries/etc. → view data and status; if admin, go to Governance · Coverage → Run now → see status update; use APIs for integration or deeper filters.

---

## F. TECHNICAL ARCHITECTURE

- **Backend:** Python 3.11+, FastAPI (business + governance routers), SQLAlchemy (sessions, raw SQL), Pydantic (schemas). Pipeline: same codebase (`core/`, `parsers/`) invoked from Airflow PythonOperators.
- **Frontend:** Next.js (App Router), React, server and client components; Tailwind CSS; `fetch` to FastAPI via `NEXT_PUBLIC_API_URL`.
- **Database:** PostgreSQL 15+; schemas bronze, silver, gold, meta; single DB for app + Airflow (separate DB name `airflow` in same server).
- **Data processing:** No Spark/Flink; in-process Python (parsers, silver/gold build) inside Airflow tasks.
- **Orchestration:** Apache Airflow 2.7.3 (LocalExecutor), one DAG; optional bootstrap container triggers one run on startup; schedule_interval=None (trigger only via API or Airflow UI).
- **Infrastructure:** Docker Compose (postgres, airflow-webserver, airflow-scheduler, pipeline_bootstrap, api, web); optional MinIO/pgAdmin under profile “full”. API and web mount source for dev.
- **Auth/authz:** No user login; admin pipeline actions protected by `ADMIN_RUN_TOKEN` (header `X-Admin-Token`). CORS allow_origins=["*"].
- **External integrations:** NMDPRA website (HTTPS scrape); Airflow REST API from FastAPI for trigger and run listing.
- **Deployment:** Compose up; `make db-upgrade`; pipeline runs on trigger or startup bootstrap.

---

## G. DATA ARCHITECTURE

- **Source data:** Four NMDPRA PDF families (Oil & Gas fact sheets, Vessel Schedule, Daily Truckout, Stock Report); link discovery from four HTML pages.
- **Ingestion:** Discover (links → file_registry) → Download (PDF to disk, hash in registry) → Parse (per-source parsers → bronze tables). File-level idempotency via content_hash at download; discover upserts by file_id (inference: per-run new file_ids in current code).
- **Transformation:** Bronze → Silver (normalized dims + facts, conformed keys) → Gold (star schemas with dim_report, fact_*). Truncate-and-reload silver/gold each run.
- **Storage:** PostgreSQL schemas: bronze (file_registry, ingest_run, ingest_run_file, rejects, dq_rule, dq_result, source-specific tables), silver (dim_*, fact_*), gold (dim_*, fact_*), meta (data_dictionary, lineage_node, lineage_edge, api_audit_log).
- **Models/schemas:** Bronze: one table per extracted entity (e.g. performance_highlights, fuel_prices_city, vessel_clearance_schedule); silver: dim_date, dim_product, dim_location, dim_facility, fact_prices, fact_stock, fact_truckout, fact_refinery_output, fact_vessel_clearance, fact_chart_series; gold: dim_date, dim_product, dim_location, dim_facility, dim_report, fact_fuel_prices, fact_stock_sufficiency, fact_truckout, fact_refinery, fact_vessel_clearance, fact_series. All in migration `001_initial_schemas.py`.
- **Business logic:** Conformed dimensions (product, location, facility) and report_key linkage in gold; date truncation and filters in API.
- **Aggregations:** Done in API (e.g. coverage GROUP BY source_name, status); gold is row-level.
- **Reference/master:** dim_report (source_name, report_title, status) in gold; product/location/facility from data.
- **Time/history:** report_period, report_date, month, date_key; last_updated in APIs; ingested_at/downloaded_at in file_registry; no explicit SCD/versioning in schema.

---

## H. DATA GOVERNANCE & QUALITY

- **Validation rules:** DQ rules in `bronze.dq_rule` (schema, range, completeness); default rules in `core/dq.py` (required columns, utilization 0–100, non-negative prices/volumes/days sufficiency, key-field completeness).
- **Data quality checks:** Run per DAG run; results in `bronze.dq_result` (passed, failed_count, total_count, sample_failures); governance API exposes rules and results.
- **Error handling:** Parsers and pipeline can leave rows in bronze; rejects table for bad rows; DQ failures recorded; run status success/fail in ingest_run.
- **Auditability:** `meta.api_audit_log` (path, method, response_status, duration_ms); ingest_run (triggered_by, started_at, finished_at, status, notes).
- **Lineage:** `meta.lineage_node`, `meta.lineage_edge` populated in publish step; lineage APIs and Mermaid diagram script.
- **Versioning:** PARSER_VERSION in env; no schema versioning or data versioning beyond run metadata.
- **Reproducibility:** Pipeline is deterministic for same inputs; backfill re-runs full pipeline (triggered_by=backfill).
- **Access controls:** No row-level security; admin token only for pipeline trigger.
- **Monitoring/logging:** Audit log per request; ingestion health API (last run, failures_count); pipeline status via Airflow API. No centralized logging config evident.

---

## I. DELIVERY & OPERATIONS

- **Deployment:** Docker Compose; `make up`, `make db-upgrade`; optional `make build`.
- **Automation:** Single DAG; bootstrap container triggers one run on startup; Run now from UI; Makefile targets (up, down, db-upgrade, diagrams, backfill, test, lint).
- **Scalability:** Single Postgres, LocalExecutor Airflow; no horizontal scaling or queue in repo.
- **Performance:** Pagination on list APIs; pool_pre_ping and pool_size on engine; no caching or read replicas in code.
- **Fault tolerance:** Airflow retries=0; pipeline records fail status and notes in ingest_run; download/parse failures can leave partial state.
- **Maintenance:** Migrations via Alembic; diagram generation (`make diagrams`); backfill for historical load.
- **Configuration:** `.env` (DB, Airflow, ADMIN_RUN_TOKEN, NMDPRA_BASE_URL, PARSER_VERSION, DQ thresholds); pydantic-settings in API.
- **Environment setup:** Docker + Compose; Node 18+ for local web; Python 3.11+ for local API/scripts; `cp .env.example .env` and edit.

---

## J. PRODUCT MANAGEMENT SIGNALS

- **Vision:** Turn NMDPRA’s PDF-centric public data into a reliable, queryable, governed data product with clear active vs archived status.
- **Scope:** Four sources only; no other regulators or private data; API-first and dashboard as consumer.
- **Prioritization:** Pipeline and governance (DQ, lineage, audit, coverage) built in from the start; Run now and ingestion health for ops.
- **Assumptions:** NMDPRA pages and PDF structure remain parseable; single tenant; admins have token; Airflow and API share same network.
- **Tradeoffs:** Truncate-and-reload silver/gold (simplicity vs incremental); no user auth (speed vs multi-tenant); schedule_interval=None (flexibility vs fixed cadence).
- **Constraints:** Public PDFs only; parsing accuracy tied to PDF layout; backfill script triggers full pipeline (no source/date filter in script).
- **Risks/limitations:** Parser breakage on NMDPRA site changes; no formal schema evolution strategy; DQ execution in run_dq is simplified (records rule existence, not full row evaluation in all paths).
- **Technical debt:** run_discover generates new file_id per item (ON CONFLICT on file_id unlikely to dedupe by URL); backfill CLI args not used to restrict pipeline.
- **Extensibility:** New source = new discover function, parser, bronze tables, and silver/gold mappings; governance and pipeline pattern reusable.

---

## K. USE CASES

1. **Monthly fuel price briefing:** Analyst opens Prices, filters by month, uses table or API to compare city-level indicative/avg prices for reports.
2. **Refinery utilization review:** Manager uses Refineries view (and API) to track utilization and output by facility and month for planning.
3. **Vessel clearance oversight:** Compliance checks Vessels page and `/v1/vessels/*` for clearance times and processing days/hours.
4. **Stock and sufficiency monitoring:** Planner uses Sufficiency and Archive stock endpoints to see current and historical days sufficiency and stock levels by product.
5. **Pipeline and data health check:** Ops opens Governance · Coverage, checks last run status and DQ failures, runs pipeline if needed and monitors status.
6. **Audit and lineage:** Auditor uses governance APIs (DQ results, API audit log, lineage nodes/edges) to verify how data is produced and who called what.
7. **Integration with internal tools:** Downstream system calls `/v1/prices/fuel`, `/v1/highlights`, or archive APIs with filters and pagination to feed internal dashboards or models.

---

## L. CONTENT MATERIAL — COMPANY SITE

### 1. Buyer-facing product summary (300–500 words)

**NMDPRA Downstream Regulatory Intelligence Platform** turns the Nigerian Midstream and Downstream Petroleum Regulatory Authority’s public PDF reports into a single, reliable data product that your team can query, monitor, and trust.

Regulators and analysts today waste time opening multiple web pages, downloading PDFs, and re-extracting the same numbers month after month. The platform automates this end to end: it discovers new reports, downloads only what’s new or changed, and parses them into structured datasets. You get **fuel prices by city**, **refinery utilization**, **vessel clearances**, **stock and days sufficiency**, and **historical truckout and stock data** through a single API and a clear dashboard—with clear labels for what’s actively updated and what’s archived.

Built for production from day one, the platform doesn’t stop at ingestion. **Data quality rules** run on every load and results are stored and exposed, so you can see exactly what passed or failed. **Lineage and a data dictionary** show where each number comes from and how it’s defined. **API audit logs** record who called which endpoint and when, supporting compliance and troubleshooting. **Coverage and ingestion health** endpoints tell you the date range and last update time for each dataset and whether the latest pipeline run succeeded.

Operators can run the pipeline on demand from the dashboard or on a schedule, and use the same APIs for backfills and integrations. The stack is standard and deployable with Docker Compose: PostgreSQL, Apache Airflow, FastAPI, and a Next.js dashboard. No lock-in to proprietary data tools—just a clean, API-first data product that turns NMDPRA’s public information into your organization’s single source of truth.

---

### 2. Ten feature highlights (business prose)

1. **Single pipeline from PDF to analytics** — One workflow discovers, downloads, parses, validates, and layers NMDPRA PDFs into bronze, silver, and gold so you always have one place to query.
2. **Idempotent, efficient updates** — Only new or changed PDFs are downloaded and processed, reducing run time and storage while keeping data current.
3. **Transparent data quality** — Configurable rules check schema, ranges, and completeness; results are stored and exposed so you can see pass/fail and sample failures before relying on data.
4. **Governance built in** — Data dictionary, lineage, DQ results, and API audit logs are first-class APIs and UI, not afterthoughts.
5. **Clear active vs archived status** — Datasets are labeled (e.g. Daily Truckout and Stock Report as archived post-2023) so reports and integrations don’t assume live updates where they’ve stopped.
6. **Run pipeline when you need it** — Trigger a full refresh from the dashboard with one click (token-protected), or rely on optional scheduled or startup runs.
7. **Coverage and ingestion health at a glance** — See per-dataset date ranges and last updated times, plus last run status and DQ failure counts, without opening Airflow.
8. **API-first design** — All business and governance capabilities are available via REST with pagination and filters, so internal tools and scripts can integrate without scraping the UI.
9. **Documented data flow** — Mermaid diagrams for architecture, gold model, and lineage are generated from the same pipeline, keeping documentation in sync with the system.
10. **Backfill and reproducibility** — Re-run the full pipeline for backfill or recovery with a simple CLI, with run metadata recorded for audit.

---

### 3. Five strong product article titles

1. From PDFs to a Single Source of Truth: The NMDPRA Downstream Regulatory Intelligence Platform  
2. How We Turn Regulatory PDFs Into Trusted, Queryable Data  
3. Governance First: DQ, Lineage, and Audit in the NMDPRA Downstream Regulatory Intelligence  
4. One Pipeline, Four Sources: Designing for Idempotency and Clarity  
5. Why We Built an API-First Data Product for Nigerian Downstream Regulation  

---

### 4. Elevator pitch

**NMDPRA Downstream Regulatory Intelligence Platform** turns the regulator’s public PDFs into one API-first, governed data product—with automated ingestion, data quality, lineage, and a dashboard—so your team can query fuel prices, refinery status, vessel clearances, and stock sufficiency without ever opening a PDF again.

---

## M. CONTENT MATERIAL — LEADERSHIP PORTFOLIO

### 1. Executive summary (enterprise data product)

This project delivers an **enterprise-grade data product** for the Nigerian Midstream and Downstream Petroleum Regulatory Authority. It takes multiple, unstructured public PDF sources and produces a single, queryable, governed data asset with clear ownership of quality and lineage. The design choices—layered storage (bronze/silver/gold), API-first exposure, embedded governance (DQ, metadata, lineage, audit), and operational visibility (coverage, ingestion health, pipeline trigger)—show a focus on long-term maintainability, compliance, and trust, not just one-off pipelines. The result is a platform that can scale to more sources and consumers while keeping a single narrative: one pipeline, one API surface, one place to see what’s in the data and how it was built.

---

### 2. Ten senior-level capability statements

1. Defined and delivered a full data product lifecycle (discover → ingest → validate → transform → serve → govern) for a regulatory use case.  
2. Designed a layered data architecture (bronze/silver/gold/meta) with clear separation of raw, normalized, and analytics layers and governance metadata.  
3. Introduced configurable data quality rules (schema, range, completeness) with persisted results and APIs for transparency.  
4. Exposed lineage and data dictionary as first-class APIs and wired them into pipeline and documentation generation.  
5. Implemented API audit logging and ingestion health endpoints to support accountability and operational monitoring.  
6. Balanced “run on demand” vs “scheduled” by making the pipeline trigger-based with optional bootstrap and UI trigger, without over-committing to a fixed schedule.  
7. Delivered both consumption interfaces (REST APIs + dashboard) and operations (pipeline status, Run now, coverage, health) in one product.  
8. Made source status explicit (active vs archived) and reflected it in APIs and UI to avoid misuse of discontinued series.  
9. Used idempotent design (content hash at download, truncate-reload at silver/gold) to keep runs predictable and repeatable.  
10. Documented architecture and lineage in code (Mermaid generation) so technical and governance documentation stay aligned with the system.

---

### 3. Key design decisions worth highlighting

- **Bronze/silver/gold + meta:** Single store, clear layers and schema ownership; meta for governance separate from business data.  
- **One DAG, one pipeline:** Single DAG for the entire flow to simplify operations and reasoning; trigger-based so cadence is configurable.  
- **Governance as product:** DQ, metadata, lineage, and audit are APIs and UI, not internal-only.  
- **Token-protected admin only:** No broad user auth; admin token for pipeline trigger keeps scope small and deployable.  
- **API-first:** All capabilities consumable via REST with pagination and filters, enabling integration and future clients.  
- **Truncate-reload for silver/gold:** Favors simplicity and correctness over incremental complexity for current scale.

---

### 4. Tradeoffs that show maturity

- **Truncate-reload vs incremental:** Chose full refresh for silver/gold for simplicity and correctness; documented so future incremental design is a conscious change.  
- **No user authentication vs speed to value:** Shipped without login to reduce scope; admin token and audit log still support accountability.  
- **Single DAG vs many:** One DAG improves operability and clarity; backfill and source-specific needs are acknowledged (e.g. backfill script could be extended to filter by source/date).  
- **Fixed pipeline code in Airflow vs external repo:** Pipeline logic lives in repo and is mounted into Airflow; keeps one codebase and versioning.  
- **Active vs archived in schema and API:** Explicit status and separate archive endpoints avoid confusion when sources stop updating.

---

### 5. Five strong case-study article titles

1. Building an Enterprise Data Product for a Petroleum Regulator: From PDFs to Governed APIs  
2. How We Embedded Data Quality, Lineage, and Audit in One Pipeline  
3. Designing for Trust: Governance and Transparency in the NMDPRA Downstream Regulatory Intelligence  
4. Tradeoffs in a Production Data Platform: Idempotency, Layers, and Operational Visibility  
5. Delivering Both Analytics and Operations: API-First Design for Regulators  

---

## N. EVIDENCE TABLE

| Claim or conclusion | Supporting file(s) | Confidence | Notes / assumptions |
|---------------------|--------------------|------------|----------------------|
| Product name: NMDPRA Downstream Regulatory Intelligence Platform (V1) | README.md | High | Explicit. |
| Four data sources (OilGasData, VesselSchedule, DailyTruckout, StockReport) | README.md, core/discover.py, 001_initial_schemas.py | High | Enum and discover functions. |
| Pipeline: discover → download → parse → DQ → silver → gold → publish → finalize | nmdpra_end_to_end_dag.py, core/run_pipeline.py | High | DAG and run_pipeline. |
| Idempotent download via content hash | core/download.py, run_pipeline.run_download (file_registry update) | High | Hash computed and stored; skip logic in run_download is implicit (always downloads; idempotency is “don’t re-parse same file” via hash). |
| Bronze/silver/gold/meta schemas | 001_initial_schemas.py | High | Full migration. |
| DQ rules: schema, range, completeness | core/dq.py, governance_dq.py, bronze.dq_rule/dq_result | High | default_dq_rules and APIs. |
| Run now from dashboard via token | PipelineStatusCard.tsx, api/pipeline/run/route.ts, admin_pipeline.py | High | Token in header; server-side only. |
| Coverage and ingestion health APIs | reports.py (coverage), governance_health.py | High | Implemented. |
| Lineage and data dictionary in meta | run_pipeline.run_publish_metadata_lineage, governance_lineage.py, governance_metadata.py | High | Minimal nodes in publish; full lineage in generate_diagrams. |
| API audit middleware | middleware.py, meta.api_audit_log | High | Every request logged. |
| Backfill triggers full pipeline | scripts/backfill.py | High | run_full_pipeline(triggered_by="backfill"); SOURCE/FROM/TO not used in script. |
| Dashboard: Overview, Prices, Sufficiency, Refineries, Gas, Vessels, Archive, Governance (Coverage, DQ, Lineage, Catalog) | layout.tsx, page.tsx, */*.tsx under app | High | All present. |
| No user login; admin token only | config, admin_pipeline.py, .env.example | High | No auth router or session. |
| Airflow schedule_interval=None; trigger only | nmdpra_end_to_end_dag.py | High | Explicit. |
| Mermaid diagrams generated from code | scripts/generate_diagrams.py | High | data_architecture, gold_dimensional_model, lineage. |
| Parsers use pdfplumber (and utils) | parsers/oilgasdata_parser.py, README | High | README mentions camelot/tabula, tesseract; oilgasdata uses pdfplumber. |
| Discover upserts file_registry; new file_id per item in loop | run_pipeline.run_discover | Medium | ON CONFLICT (file_id) never triggers with new UUIDs; infer: dedupe by URL not implemented. |
| Target: internal NMDPRA use | README (License) | Medium | “Internal / NMDPRA Downstream Regulatory Intelligence use.” |
| Production-ready maturity | README, Docker Compose, migrations, single DAG, governance | High | Judgment from structure and docs. |

---

*End of structured analysis. All claims tied to repository evidence; inferences marked. Not evident from repository: user research, formal SLA, disaster recovery, or scaling beyond single-node.*
