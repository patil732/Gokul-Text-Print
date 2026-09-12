"""
app/dashboard/alerts/__init__.py
--------------------------------
Sprint 6 — Executive BI Dashboard Operational Alert Engine Package.
"""

from app.dashboard.alerts.alert_engine import (
    AlertEngine,
    get_active_alerts,
)

__all__ = [
    "AlertEngine",
    "get_active_alerts",
]
