"""
tests/test_dashboard_reports.py
-------------------------------
Unit & Integration Tests for Executive BI Dashboard Report Generation (Sprint 6).

Covers:
  1. Generating Daily, Weekly, Monthly, and Custom reports.
  2. PDF Export for each report type: non-empty, valid PDF magic header (%PDF-).
  3. CSV Export for each report type: non-empty, contains all 7 executive sections:
     - METADATA / REPORT TITLE
     - FINANCIAL & SALES SUMMARY
     - INVENTORY SUMMARY
     - SALES FORECAST PROJECTION
     - BUSINESS HEALTH SCORE
     - AI EXECUTIVE RECOMMENDATIONS
     - OPERATIONAL ALERTS
  4. REST Endpoint GET /api/reports/generate:
     - All 4 types across both formats (PDF and CSV) return HTTP 200 with appropriate Content-Disposition.
     - Parameter validation returns HTTP 400 for invalid types or formats.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.dashboard.reports import (
    build_daily_report,
    build_weekly_report,
    build_monthly_report,
    build_custom_report,
    export_pdf,
    export_csv,
    ReportData,
)

# Load Flask app factory from app.py
_SPEC = importlib.util.spec_from_file_location("app_entry", os.path.join(_ROOT, "app.py"))
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


_EXPECTED_CSV_SECTIONS = [
    "EXECUTIVE BI REPORT",
    "FINANCIAL & SALES SUMMARY",
    "INVENTORY SUMMARY",
    "SALES FORECAST PROJECTION",
    "BUSINESS HEALTH SCORE",
    "AI EXECUTIVE RECOMMENDATIONS",
    "OPERATIONAL ALERTS",
]


# ============================================================================ #
# 1. Report Assembly & Export Unit Tests
# ============================================================================ #

class TestReportBuilders:

    def test_daily_report_assembly_and_exports(self):
        rep = build_daily_report()
        assert isinstance(rep, ReportData)
        assert rep.report_type == "Daily Report"
        assert rep.revenue > 0
        assert "total_sales" in rep.sales_summary
        assert "stock_health" in rep.inventory_summary
        assert "projected_value" in rep.forecast
        assert "score" in rep.business_health

        # PDF Export
        pdf_bytes = export_pdf(rep)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b"%PDF-"), "Expected valid PDF magic bytes"

        # CSV Export
        csv_text = export_csv(rep)
        assert isinstance(csv_text, str)
        assert len(csv_text) > 200
        for section in _EXPECTED_CSV_SECTIONS:
            assert section in csv_text, f"Missing expected section '{section}' in Daily CSV"

    def test_weekly_report_assembly_and_exports(self):
        rep = build_weekly_report()
        assert isinstance(rep, ReportData)
        assert rep.report_type == "Weekly Report"
        assert "Week of" in rep.period_label

        # PDF Export
        pdf_bytes = export_pdf(rep)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b"%PDF-")

        # CSV Export
        csv_text = export_csv(rep)
        assert isinstance(csv_text, str)
        assert len(csv_text) > 200
        for section in _EXPECTED_CSV_SECTIONS:
            assert section in csv_text, f"Missing expected section '{section}' in Weekly CSV"

    def test_monthly_report_assembly_and_exports(self):
        rep = build_monthly_report(month=9, year=2026)
        assert isinstance(rep, ReportData)
        assert rep.report_type == "Monthly Report"
        assert "Month of 2026-09" in rep.period_label

        # PDF Export
        pdf_bytes = export_pdf(rep)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b"%PDF-")

        # CSV Export
        csv_text = export_csv(rep)
        assert isinstance(csv_text, str)
        assert len(csv_text) > 200
        for section in _EXPECTED_CSV_SECTIONS:
            assert section in csv_text, f"Missing expected section '{section}' in Monthly CSV"

    def test_custom_report_assembly_and_exports(self):
        rep = build_custom_report(start_date="2026-08-01", end_date="2026-08-15")
        assert isinstance(rep, ReportData)
        assert rep.report_type == "Custom Report"
        assert "2026-08-01 to 2026-08-15" in rep.period_label

        # PDF Export
        pdf_bytes = export_pdf(rep)
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b"%PDF-")

        # CSV Export
        csv_text = export_csv(rep)
        for section in _EXPECTED_CSV_SECTIONS:
            assert section in csv_text, f"Missing expected section '{section}' in Custom CSV"


# ============================================================================ #
# 2. REST Endpoint Integration Tests (GET /api/reports/generate)
# ============================================================================ #

class TestReportEndpoint:

    @pytest.mark.parametrize("report_type", ["daily", "weekly", "monthly", "custom"])
    def test_endpoint_pdf_generation_for_all_types(self, client, report_type):
        url = f"/api/reports/generate?type={report_type}&format=pdf"
        if report_type == "custom":
            url += "&start=2026-08-01&end=2026-08-20"

        resp = client.get(url)
        assert resp.status_code == 200
        assert "application/pdf" in resp.content_type
        assert f"executive_report_{report_type}" in resp.headers.get("Content-Disposition", "")
        assert resp.data.startswith(b"%PDF-")
        assert len(resp.data) > 1000

    @pytest.mark.parametrize("report_type", ["daily", "weekly", "monthly", "custom"])
    def test_endpoint_csv_generation_for_all_types(self, client, report_type):
        url = f"/api/reports/generate?type={report_type}&format=csv"
        if report_type == "custom":
            url += "&start=2026-08-01&end=2026-08-20"

        resp = client.get(url)
        assert resp.status_code == 200
        assert "text/csv" in resp.content_type
        assert f"executive_report_{report_type}" in resp.headers.get("Content-Disposition", "")
        csv_body = resp.data.decode("utf-8")
        assert len(csv_body) > 200
        for section in _EXPECTED_CSV_SECTIONS:
            assert section in csv_body, f"Missing section '{section}' in {report_type} CSV response"

    def test_endpoint_default_parameters(self, client):
        """Default query should generate Daily report in PDF format."""
        resp = client.get("/api/reports/generate")
        assert resp.status_code == 200
        assert "application/pdf" in resp.content_type
        assert "executive_report_daily" in resp.headers.get("Content-Disposition", "")
        assert resp.data.startswith(b"%PDF-")

    def test_endpoint_invalid_type_returns_400(self, client):
        resp = client.get("/api/reports/generate?type=hourly")
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["status"] == "error"
        assert "Invalid report type" in body["message"]

    def test_endpoint_invalid_format_returns_400(self, client):
        resp = client.get("/api/reports/generate?format=xlsx")
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["status"] == "error"
        assert "Invalid export format" in body["message"]
