"""
app/dashboard/reports/__init__.py
---------------------------------
Sprint 6 — Executive BI Dashboard Report Generation Package.
"""

from app.dashboard.reports.base_report import (
    ReportData,
    export_csv,
    export_pdf,
    fetch_active_alerts,
)
from app.dashboard.reports.daily_report import build_daily_report
from app.dashboard.reports.weekly_report import build_weekly_report
from app.dashboard.reports.monthly_report import build_custom_report, build_monthly_report

__all__ = [
    "ReportData",
    "export_pdf",
    "export_csv",
    "fetch_active_alerts",
    "build_daily_report",
    "build_weekly_report",
    "build_monthly_report",
    "build_custom_report",
]
