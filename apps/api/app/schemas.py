"""Pydantic response schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict


class PaginatedMeta(BaseModel):
    page: int = 1
    per_page: int = 20
    total: int = 0
    total_pages: int = 0


class CoverageInfo(BaseModel):
    min_date: Optional[date] = None
    max_date: Optional[date] = None
    last_updated: Optional[datetime] = None
    data_status: str = "active"  # active | archived | paused


# Reports
class ReportSummary(BaseModel):
    file_id: str
    source_name: str
    report_title: Optional[str]
    report_period: Optional[date]
    report_date: Optional[date]
    status: str
    discovered_at: Optional[datetime]
    downloaded_at: Optional[datetime]


class ReportDetail(ReportSummary):
    source_page_url: str
    pdf_url: str
    content_hash: Optional[str]
    file_path: Optional[str]


# Oil & Gas
class PerformanceHighlight(BaseModel):
    month: date
    metric_name: str
    metric_value: Optional[Decimal]
    unit: Optional[str]


class RefineryStatus(BaseModel):
    month: date
    refinery_name: str
    refinery_type: Optional[str]
    capacity_bpsd: Optional[Decimal]
    utilization_pct: Optional[Decimal]
    product: Optional[str]
    status: Optional[str]


class FuelPriceCity(BaseModel):
    month: date
    city: str
    indicative_price: Optional[Decimal]
    min_price: Optional[Decimal]
    max_price: Optional[Decimal]
    avg_price: Optional[Decimal]
    unit: Optional[str]


class ChartSeriesValue(BaseModel):
    chart_name: str
    series_name: str
    period_type: str
    period_date: Optional[date]
    period_month: Optional[date]
    value: Decimal
    unit: Optional[str]


# Vessels
class VesselClearance(BaseModel):
    report_period: date
    clearance_no: Optional[str]
    company: Optional[str]
    vessel_name: Optional[str]
    processing_days: Optional[Decimal]
    processing_hours: Optional[Decimal]
    clearance_ts: Optional[datetime]


# Governance
class DQRule(BaseModel):
    rule_id: str
    rule_name: str
    layer: str
    table_name: str
    rule_type: str
    severity: str
    is_active: bool


class DQResult(BaseModel):
    result_id: str
    run_id: Optional[str]
    layer: str
    table_name: str
    rule_id: Optional[str]
    passed: bool
    failed_count: int
    total_count: int
    sample_failures: Optional[List[dict]]
    created_at: Optional[datetime]


class DataDictionaryEntry(BaseModel):
    id: str
    object_type: str
    object_name: str
    description: Optional[str]
    data_type: Optional[str]
    owner: Optional[str]
    tags: Optional[List[str]]


class LineageNode(BaseModel):
    node_id: str
    layer: str
    object_name: str
    object_type: str


class LineageEdge(BaseModel):
    id: str
    from_node_id: str
    to_node_id: str
    transform_name: Optional[str]
    transform_version: Optional[str]


class ApiAuditEntry(BaseModel):
    id: str
    request_id: Optional[str]
    path: str
    method: str
    response_status: Optional[int]
    duration_ms: Optional[int]
    created_at: Optional[datetime]


class IngestionHealth(BaseModel):
    last_run_id: Optional[str]
    last_run_status: Optional[str]
    last_run_finished_at: Optional[datetime]
    failures_count: int = 0
    coverage_drift: Optional[str] = None
