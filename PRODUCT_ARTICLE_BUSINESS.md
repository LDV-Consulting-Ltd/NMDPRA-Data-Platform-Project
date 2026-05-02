# NMDPRA Downstream Regulatory Intelligence Platform: From PDFs to a Single Source of Truth

*One platform for Nigerian downstream petroleum data—queryable, governed, and ready for decisions*

---

## 1. Opening Problem Statement

The Nigerian Midstream and Downstream Petroleum Regulatory Authority (NMDPRA) publishes essential metrics every month: fuel prices by city, refinery utilization, vessel clearances, stock levels, and days of supply. That information drives policy, planning, and compliance—but today it lives as PDFs on several web pages. Teams either open each report manually, re-typing numbers into spreadsheets and briefings, or build one-off scrapers that break when the regulator changes a layout. There is no single place to see what data exists, when it was last updated, or whether the numbers are complete and consistent. The result is duplicated effort, delayed decisions, and a real risk of using outdated or misinterpreted data.

The gap is not lack of publication; it is the step from “published” to “usable as a product.” The NMDPRA Downstream Regulatory Intelligence Platform closes that gap by turning the regulator’s public PDFs into one authoritative, queryable data product with clear quality and provenance—so your organization can rely on it for decisions, reporting, and integration.

---

## 2. What the Product Is

The NMDPRA Downstream Regulatory Intelligence Platform is a **production-ready, API-first data platform** that ingests, cleans, and serves NMDPRA public data with built-in governance and a web dashboard. It does not replace the regulator’s publication; it sits on top of it. The platform automatically discovers new and updated reports from four NMDPRA sources (Oil & Gas fact sheets, Vessel Schedule, Daily Truckout, and Stock Report), downloads only what has changed, extracts structured data from the PDFs, runs data quality checks, and layers the results into normalized datasets. You then access everything through REST APIs and a single dashboard—with clear labels for which datasets are actively updated and which are archived (for example, Daily Truckout and Stock Report after 2023).

The platform is built for production from day one: it includes database migrations, a single automated pipeline, governance APIs (data quality, lineage, metadata, audit), and operational visibility so you can see coverage and pipeline health without opening separate tools. It is deployable with standard infrastructure (PostgreSQL, orchestration, API server, web app) and does not depend on proprietary data platforms.

---

## 3. Who It Is For

The platform is designed for **decision-makers, analysts, operators, and partners** who need NMDPRA data in a reliable, repeatable form.

**Regulators and policy teams** can use it as the single source for fuel prices, refinery performance, vessel clearances, and stock sufficiency when preparing briefings, reports, and policy decisions—without manually re-extracting from PDFs.

**Operations and data teams** get one pipeline to run and monitor: they can see coverage per dataset, last run status, and data quality results in the dashboard, trigger a refresh on demand, and use the same APIs for backfills or integrations.

**Compliance and audit** can verify how data was produced and who used it: data quality results, lineage, and API audit logs are exposed through governance APIs, so traceability and accountability are built in.

**Technical buyers and partners** can integrate via REST: every business and governance capability is available through documented APIs with pagination and filters, so internal tools, dashboards, or models can consume the data without scraping the web interface.

**Beta users and evaluators** can run the platform in a standard environment, try the dashboard and APIs, and assess fit for their workflows before committing to a full rollout.

---

## 4. Core Capabilities

The platform delivers a defined set of capabilities, all in place and usable today.

**Automated discovery and ingestion.** The system discovers PDF links from the four NMDPRA pages, infers report period or date where possible, and downloads only new or changed files (using content hashes to skip unchanged PDFs). That reduces run time and keeps data current without re-processing the same reports every time.

**Structured extraction.** Source-specific parsers turn each PDF type into structured tables: performance highlights, refinery status, fuel prices by city, vessel clearances, truckout by depot and state, and stock and days-sufficiency data. Every row is tied to its source report and page for traceability.

**Data quality.** Configurable rules check that required fields exist, numeric values sit in valid ranges (for example utilization 0–100, non-negative prices and volumes), and key fields are complete. Results are stored and exposed—you can see pass/fail, failure counts, and sample failures before relying on the data. Rows that fail validation can be routed to a rejects store for review.

**Layered data model.** Raw extraction lands in a “bronze” layer; normalized dimensions and facts sit in “silver”; analytics-ready star schemas sit in “gold.” That separation keeps raw data auditable while giving you a clean, consistent surface for reporting and APIs.

**Business and governance APIs.** Business APIs serve reports, highlights, fuel prices, refineries, gas, vessels, archive data (truckout and stock), and chart series—all with pagination and filters (e.g. by month, city, or date range). Governance APIs serve coverage (date range and last updated per dataset), ingestion health (last run status and failure counts), data quality rules and results, lineage (how data flows from source to table), a data dictionary, and an API audit log (who called what and when).

**Dashboard and operations.** A web dashboard provides an overview, dedicated views for prices, sufficiency, refineries, gas, vessels, and archived data, plus governance sections for coverage, data quality, lineage, and the data dictionary. Operators can see pipeline status and trigger a full refresh from the dashboard (with appropriate access control) so that running and monitoring the pipeline does not require a separate orchestration UI.

**Active vs archived.** Datasets are explicitly labeled as active or archived. Daily Truckout and Stock Report are marked archived (last published 2023) so that reports and integrations do not assume live updates where the regulator has stopped publishing.

---

## 5. How It Works

The platform runs as a single pipeline: **discover → download → parse → validate → transform → publish**.

First, the system scans the four NMDPRA pages, collects PDF links and any available period or date information, and registers them in a file registry. It then downloads each PDF (skipping those that have not changed, using a content hash), and runs the appropriate parser for each source. Extracted rows are written into bronze tables with source and page references. Next, data quality rules run on the bronze layer; results are stored and exposed so you can see what passed or failed. Only then does the pipeline build the silver layer (normalized dimensions and facts) and the gold layer (star schemas with a report dimension so every fact is tied to its source and status). A final step publishes metadata and lineage so that governance APIs and documentation reflect the current flow.

The pipeline can be triggered on demand from the dashboard, on a schedule, or at startup—so you can align refresh cadence with your operational needs. All business and governance data is served through REST APIs; the dashboard is one client of those APIs. Pagination and filters are available on list endpoints so that both human users and downstream systems can query efficiently. Deployment uses standard components (PostgreSQL, an orchestrator, API server, web app) and can be brought up with a single command and a database migration step.

---

## 6. Practical Use Cases

**Monthly fuel price briefing.** An analyst opens the Prices view or calls the fuel-prices API filtered by month, compares city-level indicative and average prices, and uses the result in a briefing or report—without opening a single PDF.

**Refinery utilization and planning.** A manager uses the Refineries view or API to track utilization and output by facility and month for operational and capacity planning.

**Vessel clearance oversight.** A compliance officer checks the Vessels view or API for clearance times and processing days/hours to verify that clearances are being issued and processed within expected timelines.

**Stock and days sufficiency.** A planner uses the Sufficiency view and archive stock endpoints to see current and historical days sufficiency and stock levels by product for supply and demand analysis.

**Pipeline and data health.** An operator opens the Governance · Coverage section, sees last run status and data quality failure counts, and triggers a refresh if needed—all from the same place as the rest of the platform.

**Audit and compliance.** An auditor uses governance APIs to review data quality results, lineage (how data moved from source to table), and the API audit log (which endpoints were called and when) to verify how data was produced and consumed.

**Integration.** A downstream system calls the fuel-prices, highlights, or archive APIs with filters and pagination to feed internal dashboards, models, or reports—using the platform as the single source for NMDPRA data.

---

## 7. Why It Matters

The value is in **trust and reuse**. Today, NMDPRA data is authoritative but hard to use at scale; the platform makes it queryable and traceable. Decisions—policy, planning, compliance—can be based on a known pipeline and visible quality checks instead of ad hoc extraction. Duplicate work drops because one pipeline and one API surface serve many consumers. Operational risk is reduced because bad or incomplete data is flagged by rules and stored in results and rejects; lineage and audit logs support accountability and troubleshooting.

For partners and technical buyers, the platform offers a clear contract: REST APIs, documented behavior, and governance that is part of the product rather than an afterthought. For the organization, it turns “we have PDFs” into “we have a data product”—one that can be extended to more sources or consumers without re-architecting, because the layers (raw, normalized, analytics, governance) and the API-first design are already in place.

---

## 8. Closing / Call to Action

The NMDPRA Downstream Regulatory Intelligence Platform is built to be the single, authoritative layer over the regulator’s public PDFs: automated ingestion, transparent data quality, lineage and audit, and a dashboard and APIs that support both daily use and integration. It is production-ready, evidence-based in its capabilities, and designed so that your team can rely on it for decisions and reporting.

If you are a decision-maker, partner, technical buyer, or operational stakeholder looking for a practical way to turn NMDPRA’s published data into a queryable, governed data product—without manual re-entry or fragile scripts—the platform is built for you. Deploy it in your environment, try the dashboard and APIs, and use the governance views to see exactly what data you have and how it was built. For more detail on capabilities, integration, or deployment, reach out to discuss your use case and how the platform can support it.

---

*Approx. 1,500 words.*
