"""
app/dashboard/analytics package
-------------------------------
Sprint 6 — Executive BI Dashboard Analytics Engines:
  - sales_analytics.py: Revenue trends, volume, product performance, and prediction history
  - inventory_analytics.py: Stock trends, turnover velocity, low stock, and dead stock analysis
"""

from app.dashboard.analytics.sales_analytics import get_sales_analytics
from app.dashboard.analytics.inventory_analytics import get_inventory_analytics
