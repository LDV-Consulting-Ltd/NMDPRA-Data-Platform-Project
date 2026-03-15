# Building an Enterprise Data Product for a Petroleum Regulator: The NMDPRA Data Platform

*A case study in data product management, platform design, and governed delivery*

---

## 1. Executive Context and Industry Problem

Regulators in oil and gas sit on some of the most policy-sensitive data a country produces: fuel prices by city, refinery utilization, vessel clearances, stock levels, and days of supply. In Nigeria, the Nigerian Midstream and Downstream Petroleum Regulatory Authority (NMDPRA) publishes these metrics as PDFs on several public web pages—Oil & Gas fact sheets, vessel schedules, daily truckout reports, and stock and days-sufficiency reports. The information is authoritative and public, but it is not structured, queryable, or easy to reuse. Analysts and policy teams either manually open PDFs every month or build one-off scrapers that break when layouts change. There is no single place to see what data exists, when it was last updated, or whether the numbers are complete and consistent. The result is duplicated effort, delayed decisions, and a higher risk of using outdated or misinterpreted data.

The problem is not lack of data; it is the gap between “published” and “usable as a product.” Turning PDF-centric publication into a reliable, queryable data product requires more than parsing: it requires a clear ingestion strategy, defined layers of storage, explicit quality checks, traceable lineage, and interfaces that support both human users and downstream systems. This case study describes how the NMDPRA Data Product Platform was designed and delivered to close that gap—and what that implies for enterprise data product management and end-to-end delivery.

---

## 2. Product Vision and Strategic Intent

The vision was to make NMDPRA’s public data a single, authoritative, queryable asset with known quality and provenance—not a one-off report or a fragile script, but a **data product**: something the organization could rely on for decisions, reporting, and integration. That meant treating the pipeline (discover, download, parse, validate, transform, serve) and the consumption surface (APIs and dashboard) as one product, and treating governance—data quality, lineage, metadata, and audit—as part of the product from the start, not an add-on.

Strategic intent showed up in three ways. First, **API-first**: every capability that matters for consumption or oversight is exposed via REST, with pagination and filters, so that internal tools, reports, and future clients can integrate without depending on the UI. Second, **governance as product**: data quality rules and results, lineage, a data dictionary, and API audit logs are first-class APIs and dashboard sections, so that trust and compliance are visible and usable. Third, **explicit lifecycle**: sources are labeled as active or archived (e.g. Daily Truckout and Stock Report after 2023), so that reports and integrations do not assume live updates where the regulator has stopped publishing. The product was scoped to four NMDPRA sources and internal use; the architecture was chosen so that adding sources or consumers would not require rethinking the model.

---

## 3. Stakeholders, Users, and Decision Environment

The primary audience is internal: regulators, analysts, and operations staff who need current and historical NMDPRA metrics for policy, planning, compliance, and reporting. The platform does not implement role-based access control or a login UI; the distinction in the current build is between **read-only users** (dashboard and APIs) and **operators** who can trigger the pipeline via a token-protected “Run now” action. That choice kept scope manageable while still supporting accountability: every API call is logged to an audit table, and pipeline runs record who triggered them (e.g. startup, manual, backfill).

The decision environment is characteristic of regulation: decisions depend on timely, consistent data (e.g. fuel prices by city and month, refinery utilization, vessel clearance times, stock and days sufficiency). Before the platform, those decisions were fed by manual PDF extraction or ad hoc scripts. After, they can be fed by filtered API calls and dashboard views, with coverage and last-updated information visible so that users know what they are looking at. The product is built to support **decision systems**—policy briefings, compliance checks, operational monitoring—not only ad hoc exploration. Auditors and data stewards are served by governance APIs (DQ results, lineage, audit log) so that how data was produced and who used it can be verified without opening the pipeline code.

---

## 4. Problem Decomposition

The high-level problem—“turn NMDPRA PDFs into a trusted, queryable data product”—was broken into six subproblems, each addressed by a defined part of the system.

**Discovery.** The regulator’s pages list PDFs with varying naming and date cues. The system had to find all relevant links, infer report period or date where possible, and register them in a file registry so that downstream steps could decide what to download and parse. This is implemented as source-specific discover functions (one per NMDPRA page) that scrape HTML, extract PDF links, and normalize metadata into a common structure.

**Ingestion and idempotency.** Downloading and parsing everything on every run would be wasteful and brittle. The design uses a **content hash** on downloaded PDFs and stores it in the file registry; the pipeline can skip re-processing unchanged files. Silver and gold layers use **truncate-and-reload** each run: simpler than incremental logic at current scale and easier to reason about for correctness.

**Extraction.** PDFs differ by source (fact sheets vs vessel schedules vs daily truckout vs stock reports). Each source has a dedicated parser that maps tables and text into bronze tables with a consistent pattern: entity tables plus source_file_id and source_page for traceability. Parsing is in-process Python (e.g. pdfplumber); the same code runs in the orchestration layer so that one codebase owns the logic.

**Quality and remediation.** Raw extraction can produce missing or invalid values. Before data is promoted to silver and gold, configurable **data quality rules** run on bronze (schema, range, completeness). Results are stored (pass/fail, counts, sample failures) and exposed via governance APIs; a rejects table exists for bad rows. This gives a clear before/after boundary: bronze can be messy; silver and gold are built only from validated context.

**Modeling and serving.** Bronze is source-shaped; silver normalizes into conformed dimensions (date, product, location, facility) and facts; gold is a star schema (dim_report plus fact tables) for analytics and API exposure. Business and governance APIs read from these layers so that consumers see a stable, documented surface.

**Operational visibility.** Operators and data stewards need to see pipeline status, coverage per dataset, last run outcome, and DQ failures without logging into the orchestrator. The product includes coverage APIs, ingestion-health endpoints, a pipeline-status card on the dashboard, and a token-protected “Run now” so that refresh and monitoring live in the same place as consumption.

This decomposition drove the pipeline (discover → download → parse → DQ → silver → gold → publish → finalize) and the split between bronze, silver, gold, and meta schemas.

---

## 5. Product Scope and Design Choices

Scope was deliberately bounded: **four NMDPRA sources** (OilGasData, VesselSchedule, DailyTruckout, StockReport), **one pipeline**, **one API surface**, **one dashboard**. No other regulators, no private or licensed data, no generic “data lake” for unrelated datasets. That allowed the design to be coherent and production-ready instead of generic.

Several design choices are worth calling out.

**Layered storage (bronze / silver / gold / meta).** Raw extraction lands in bronze with source_file_id and source_page on every row. Silver adds conformed dimensions and fact tables; gold adds a report dimension and star-style fact tables keyed for analytics. Meta holds governance artifacts: data dictionary, lineage nodes and edges, API audit log. Separating meta from business data keeps governance queryable and auditable without mixing it into reporting models.

**One DAG, trigger-based cadence.** The entire flow is a single Airflow DAG with no fixed schedule (schedule_interval=None). Runs are triggered by API (including “Run now” from the dashboard), by an optional bootstrap run on startup, or manually in the Airflow UI. That avoids over-committing to a cadence before the organization’s rhythm is clear and keeps operations simple: one pipeline to monitor and one place to look for failures.

**Governance as product.** Data quality rules and results, lineage, the data dictionary, and the API audit log are not internal-only. They are exposed via REST and through governance sections of the dashboard (Coverage, DQ, Lineage, Catalog). The same pipeline that builds business data also publishes lineage metadata and supports diagram generation (e.g. Mermaid) so that documentation and system stay aligned.

**Token-protected admin only.** There is no broad user-authentication system. Pipeline trigger is protected by an admin token (server-side only, never sent to the browser); read access to APIs and dashboard is open within the deployment. This traded off multi-tenant auth for speed to value while still retaining accountability through audit logging and run metadata.

**API-first.** All list and detail endpoints support pagination and, where it matters, filters (e.g. month, city, date range). The dashboard is a consumer of these APIs; it does not talk to the database directly. That keeps a single contract for data and makes it clear that the product is the API; the UI is one client.

---

## 6. Capability Design

The product delivers a defined set of capabilities, each tied to a clear job.

**Discovery and download.** The pipeline discovers PDF links from four NMDPRA pages, infers report period or date from link text or URL where possible, and upserts into a file registry. It then downloads PDFs into a structured directory, computes a content hash, and updates the registry. Implemented behavior is idempotent at the file level via hash; re-running does not re-parse unchanged files.

**Source-specific parsing.** Four parser modules map PDFs to bronze tables: Oil & Gas (performance highlights, refinery status, fuel prices, gas infra, chart series), Vessel Schedule (clearance schedule), Daily Truckout (by depot, by state, totals), Stock Report (sufficiency summary, stock ledger). Each table carries source_file_id and source_page for lineage. Parsing is deterministic for a given PDF; parser version is configurable via environment.

**Data quality.** Default rules cover required columns (schema), numeric ranges (e.g. utilization 0–100, non-negative prices and volumes), and completeness of key fields. Rules are stored in bronze (dq_rule, dq_result); the pipeline runs them each DAG run and records results. Governance APIs expose rules and results so that pass/fail and sample failures are visible before data is treated as reliable.

**Silver and gold build.** Silver builds conformed dimensions (date, product, location, facility) from distinct values in bronze and maps source tables into normalized facts. Gold builds star schemas from silver, adding a report dimension (source_name, report_title, status) so that every fact can be tied to its source and lifecycle. Build is truncate-and-reload for simplicity and reproducibility.

**Business and governance APIs.** Business APIs serve reports, highlights, prices, refineries, gas, vessels, archive (truckout and stock), and charts—all with pagination, filters where relevant, and a consistent envelope (data, meta, last_updated, data_status). Governance APIs serve coverage, ingestion health, DQ rules and results, lineage nodes and edges, metadata dictionary, and API audit log. All are REST; the dashboard and any future client use the same surface.

**Pipeline operations.** Operators see pipeline status (last run, state) and ingestion health (last run ID, status, finished time, DQ failure count) on the dashboard. “Run now” triggers the DAG via the FastAPI admin endpoint (with token) and Airflow REST API; the token is never exposed to the browser. Optional bootstrap on startup can run the pipeline once when the stack comes up.

**Active vs archived.** Daily Truckout and Stock Report are explicitly marked archived (last published 2023). The schema and APIs carry this status; the dashboard has a dedicated Archive section and labels so that consumers do not assume ongoing updates for discontinued series.

These capabilities were implemented and shipped; they are not aspirational. Gaps that remain (e.g. discover deduplication by URL, backfill filtered by source/date in code) are documented in the analysis as known limits or technical debt.

---

## 7. Data Architecture and Platform Design

The data architecture is built around four PostgreSQL schemas and one orchestrated pipeline.

**Bronze** holds the system of record for ingestion: file_registry (discovered links, URLs, hashes, paths, status), ingest_run and ingest_run_file (run metadata and per-file outcomes), rejects (rows that failed validation), dq_rule and dq_result (rules and run results), and one table per extracted entity (performance_highlights, refinery_status, fuel_prices_city, vessel_clearance_schedule, truckout_*, stock_*, etc.). Every bronze row that comes from a PDF carries source_file_id and source_page so that lineage is traceable.

**Silver** holds normalized dimensions (dim_date, dim_product, dim_location, dim_facility) and facts (fact_prices, fact_stock, fact_truckout, fact_refinery_output, fact_vessel_clearance, fact_chart_series) with foreign keys to those dimensions. Silver is built from bronze in one pass per run; dimensions are derived from distinct values in the source data.

**Gold** holds the analytics-facing model: the same dimensions (with key naming suited to star schema), dim_report (source_name, report_title, status), and fact tables (fact_fuel_prices, fact_stock_sufficiency, fact_truckout, fact_refinery, fact_vessel_clearance, fact_series) each linked to dim_report so that every fact is tied to a source and its lifecycle. Gold is built strictly from silver so that there is a single transformation path.

**Meta** holds governance and operations: data_dictionary (object type, name, description, data type, owner, tags), lineage_node and lineage_edge (for pipeline and diagram generation), and api_audit_log (request path, method, response status, duration). These are written by the pipeline (e.g. publish step) or by middleware (audit log); they are read by governance APIs and the dashboard.

The platform design is deliberately standard: PostgreSQL for all layers, Airflow for orchestration (LocalExecutor), FastAPI for APIs, Next.js for the dashboard. Pipeline logic lives in the same repository as the API and is mounted into Airflow so that one codebase and one version control story apply. There is no separate “data lake” engine; the product is a single store with clear layers and a single pipeline. That reduces moving parts and keeps the narrative simple: one pipeline, one API surface, one place to see what is in the data and how it was built.

---

## 8. Data Modeling, Business Logic, and Governance

The data model follows a consistent pattern: bronze is source-shaped and append-oriented; silver is normalized with conformed dimensions; gold is star schema with a report dimension. Business logic lives in the build steps (silver and gold) and in the API layer (filters, date truncation, coverage aggregation). There is no business logic in the database beyond constraints and keys; calculations and aggregations are either in the pipeline or in the API so that they are versioned and testable.

Governance is implemented, not assumed. **Data quality**: rules are defined (schema, range, completeness) and stored; the pipeline runs them and persists results with pass/fail, counts, and sample failures. **Lineage**: nodes and edges are written in the publish step and exposed via APIs; a separate script generates Mermaid diagrams (architecture, gold model, lineage) from the same conceptual model so that docs and system stay in sync. **Metadata**: a data dictionary (meta) is populated and exposed via the governance catalog API so that object types, names, descriptions, and tags are queryable. **Audit**: every API request is logged (path, method, response status, duration) in meta.api_audit_log; pipeline runs record triggered_by, started_at, finished_at, status, and notes. **Lifecycle**: source status (active/archived) is in the schema and in API responses so that consumers can distinguish live from discontinued series.

What is not in place today: no row-level security, no formal schema-versioning or data-versioning beyond run metadata, and no centralized logging configuration beyond the audit table. The DQ execution path in the pipeline records rule existence and results; full row-level evaluation for every rule in every run is a possible extension. These boundaries are explicit so that future work can extend governance without pretending it was already there.

---

## 9. Delivery Model, Tradeoffs, and Operationalization

Delivery is Docker Compose–based: one compose file brings up Postgres, Airflow (webserver and scheduler), an optional bootstrap container that can trigger one run on startup, the FastAPI API, and the Next.js app. Migrations are Alembic; `make db-upgrade` applies them. The pipeline runs when triggered (API, UI, or Airflow UI); there is no fixed schedule in code, which keeps the organization free to set cadence later (e.g. daily or weekly) without changing the product.

Several tradeoffs were made deliberately.

**Truncate-and-reload vs incremental for silver/gold.** Full refresh each run was chosen for simplicity and correctness. Incremental loads would add complexity (merge keys, change detection, late-arriving data) that was not justified at current scale. The tradeoff is documented so that a future move to incremental is a conscious design change, not a default.

**No user authentication vs speed to value.** Shipping without a full auth system (login, roles, permissions) kept scope smaller and allowed the product to go live faster. Accountability is still provided by the admin token for pipeline trigger, run metadata (who/what triggered), and API audit log. The tradeoff is acceptable for an internal, single-tenant deployment; multi-tenant or external access would require a different auth model.

**Single DAG vs many.** One DAG for the full flow simplifies operations and debugging. Backfill and source-specific runs are possible (e.g. via backfill script or future filtering by source/date); the current backfill path runs the full pipeline and records triggered_by=backfill. The design does not preclude adding more targeted DAGs later if the organization needs them.

**Pipeline code in repo vs external.** The pipeline lives in the same repository as the API and is mounted into Airflow. That gives one codebase, one versioning story, and one place to change discovery, parsing, or transformation. The tradeoff is that Airflow and the app share a view of the codebase; that was preferred over copying or syncing logic elsewhere.

**Active vs archived in schema and API.** Rather than leaving “discontinued” implicit, the model and APIs make status explicit. Archive endpoints and UI sections exist so that historical series remain available without implying they are still updated. That avoids misuse in reports and integrations and reflects how regulators often stop publishing some series while keeping others live.

Operationalization is supported by: coverage and ingestion-health APIs; pipeline status and “Run now” in the dashboard; Makefile targets (up, down, db-upgrade, diagrams, backfill, test, lint); and configuration via environment (database URL, Airflow and API URLs, admin token, parser version, DQ thresholds). There are no retries configured on the DAG today; failures are recorded in ingest_run with status and notes so that operators can see what failed and why. Scaling (e.g. read replicas, distributed execution) is not in scope for the current deployment; the design is consistent with a single-node, production-ready footprint.

---

## 10. Outcomes, Strategic Value, and Future Evolution

The platform delivers a single, API-first, governed data product over NMDPRA’s public PDFs. Outcomes that are **implemented** include: one pipeline from discovery through gold and metadata publish; idempotent download and truncate-reload silver/gold; configurable DQ with stored results and governance APIs; lineage and data dictionary exposed and used for diagram generation; API audit logging; coverage and ingestion health visible in the dashboard; pipeline trigger from the UI with token protection; and clear active/archived treatment for sources. Analysts can query fuel prices, refinery status, vessel clearances, and stock/sufficiency via API or dashboard; operators can see coverage and run status and trigger a refresh without touching Airflow; auditors and stewards can inspect DQ results, lineage, and API usage.

Strategic value is in **trust and reuse**: one place to see what data exists, when it was updated, and how it was produced. Decisions (policy, planning, compliance) can be grounded in a known pipeline and known quality rather than ad hoc extraction. The product is built so that **future evolution** is straightforward: add a new source by adding a discover function, a parser, and bronze/silver/gold mappings; add a new consumer by calling existing APIs or adding a client; tighten governance by expanding DQ rules or lineage; change cadence by configuring schedule or triggers. The architecture does not assume a single use case or a fixed set of users; it assumes that the data product will grow in sources and consumers while keeping one pipeline and one contract.

What has not been built (and is not claimed): formal SLAs, disaster recovery playbooks, horizontal scaling, user-facing auth, or backfill filtered by source/date in the current script. Those are appropriate next steps when the organization’s needs justify them.

---

## 11. Leadership Reflection

Building this product reinforced a few principles that generalize beyond this project.

**Treat the data product as a decision system.** The goal was not “a pipeline” or “a dashboard” but a system that supports decisions—policy, compliance, operations—with timely, consistent, traceable data. That meant designing for coverage visibility, quality transparency, and lifecycle (active/archived) from the start, so that the product could be trusted and reused.

**Governance is part of the product.** Data quality, lineage, metadata, and audit were not afterthoughts. They are exposed through the same APIs and UI as business data, so that trust and compliance are usable, not hidden. That required product and technical choices (meta schema, governance routers, diagram generation) to be made upfront.

**Make tradeoffs explicit.** Truncate-reload, no user auth, single DAG, trigger-based schedule—each was a deliberate choice with a documented tradeoff. Being clear about what was chosen and what was deferred (e.g. incremental loads, backfill filtering) keeps the product honest and makes future evolution a matter of revisiting those tradeoffs, not discovering them late.

**One pipeline, one API, one narrative.** Keeping a single DAG, a single store with clear layers, and a single API surface made it possible to explain the system in one sentence and to operate it without chasing multiple pipelines or inconsistent contracts. That simplicity is a product decision as much as a technical one.

**Ship production-ready, not “MVP.”** The deliverable includes migrations, orchestration, governance APIs, and operational visibility—not a proof-of-concept that would need to be rebuilt for production. Scoping to four sources and internal use made it feasible to deliver something that could be run and maintained from day one.

For hiring managers and leaders evaluating data product capability: this project demonstrates end-to-end ownership—from problem decomposition and product vision through data architecture, governance design, delivery model, and operationalization—with explicit tradeoffs and a clear separation between what was built and what was intentionally left for later. It is offered as evidence that enterprise data products can be designed and delivered with both technical rigor and product discipline.

---

*Word count: approximately 3,050.*
