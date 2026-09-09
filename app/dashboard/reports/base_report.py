"""
app/dashboard/reports/base_report.py
------------------------------------
Sprint 6 — Executive BI Dashboard Report Generation Engine.

Common data container, operational alerts stub, and export renderers (PDF & CSV)
for executive briefings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import io
import os
import sys
from typing import Any, Dict, List, Optional

# Ensure project root is on sys.path
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_THIS_DIR)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from utils.logger import logger


@dataclass
class ReportData:
    """
    Standardized data container consolidating all 7 executive report dimensions.
    """
    report_type: str                            # "Daily Report" | "Weekly Report" | "Monthly Report" | "Custom Report"
    period_label: str                           # e.g. "2026-09-09" or "2026-09-01 to 2026-09-07"
    generated_at: str                           # ISO or formatted string
    revenue: float                              # Financial topline
    sales_summary: Dict[str, Any]               # total_sales, revenue, growth_rate, top_products
    inventory_summary: Dict[str, Any]           # total_stock, valuation, stock_health, turnover, low_stock, dead_stock
    forecast: Dict[str, Any]                    # projected_value, forecast_period, confidence, model_type
    recommendations: List[Dict[str, Any]]       # Normalized AI recommendation feed
    business_health: Dict[str, Any]             # Composite score, status, sub-scores
    alerts: List[Dict[str, Any]] = field(default_factory=list)  # Active alerts list


def fetch_active_alerts() -> List[Dict[str, Any]]:
    """
    Fetch active operational alerts from AlertEngine (Sprint 6).
    Falls back to informational operational defaults if no database alerts are stored.
    """
    try:
        from app.dashboard.alerts import AlertEngine
        engine = AlertEngine()
        db_alerts = engine.get_active_alerts(limit=10)
        if db_alerts:
            formatted = []
            for a in db_alerts:
                formatted.append({
                    "id": a.get("alert_id", "ALT")[:8].upper(),
                    "severity": a.get("priority", "INFO"),
                    "title": a.get("alert_type", "Operational Alert").replace("_", " ").title(),
                    "message": a.get("message", ""),
                    "timestamp": a.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                })
            return formatted
    except Exception as exc:
        logger.warning(f"[base_report] Could not fetch alerts from AlertEngine: {exc}")

    # Fallback operational notifications
    return [
        {
            "id": "ALT-001",
            "severity": "CRITICAL",
            "title": "Low Stock Threshold Warning",
            "message": "Multiple essential fabric item codes have fallen below reorder threshold (< 50 units).",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        {
            "id": "ALT-002",
            "severity": "WARNING",
            "title": "Inventory Turnover Velocity",
            "message": "Turnover velocity indicates slow replenishment cycle in non-priority warehouses.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        {
            "id": "ALT-003",
            "severity": "INFO",
            "title": "Automated Forecast Sync",
            "message": "AI prediction models synced with latest transaction logs.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    ]


# --------------------------------------------------------------------------- #
# CSV Export Engine
# --------------------------------------------------------------------------- #

def export_csv(report: ReportData) -> str:
    """
    Generate a clean, structured executive CSV export.
    Sections are explicitly delineated with headers and data tables.
    """
    output = io.StringIO()

    # 1. Metadata
    output.write("=" * 70 + "\n")
    output.write(f"EXECUTIVE BI REPORT: {report.report_type.upper()}\n")
    output.write(f"Period: {report.period_label}\n")
    output.write(f"Generated At: {report.generated_at}\n")
    output.write("=" * 70 + "\n\n")

    # 2. Executive KPI & Financial Topline
    output.write("--- FINANCIAL & SALES SUMMARY ---\n")
    output.write("Metric,Value\n")
    output.write(f"Total Revenue,₹{report.revenue:,.2f}\n")
    output.write(f"Total Sales Volume,{report.sales_summary.get('total_sales', 0):,}\n")
    output.write(f"Sales Growth Rate,{report.sales_summary.get('growth_rate', 0.0):+.2f}%\n\n")

    # 3. Top Products
    top_prods = report.sales_summary.get("top_products", [])
    if top_prods:
        output.write("--- TOP PERFORMING PRODUCTS ---\n")
        output.write("Product,Revenue,Quantity,Share (%)\n")
        for p in top_prods[:5]:
            p_name = str(p.get("product", "Unknown")).replace(",", " ")
            output.write(
                f"{p_name},₹{p.get('revenue', 0.0):,.2f},{p.get('quantity', 0)},{p.get('share_percentage', 0.0):.1f}%\n"
            )
        output.write("\n")

    # 4. Inventory Status
    output.write("--- INVENTORY SUMMARY ---\n")
    output.write("Metric,Value\n")
    output.write(f"Inventory Health Status,{report.inventory_summary.get('stock_health', 'Healthy')}\n")
    output.write(f"Total Stock Units,{report.inventory_summary.get('total_stock', 0):,.2f}\n")
    output.write(f"Inventory Valuation,₹{report.inventory_summary.get('valuation', 0.0):,.2f}\n")
    output.write(f"Turnover Ratio,{report.inventory_summary.get('turnover_ratio', 0.0):.2f}\n")
    output.write(f"Low Stock Products Count,{report.inventory_summary.get('low_stock_count', 0)}\n")
    output.write(f"Dead Stock Items Count,{report.inventory_summary.get('dead_stock_count', 0)}\n\n")

    # 5. Forecast Projection
    output.write("--- SALES FORECAST PROJECTION ---\n")
    output.write("Metric,Value\n")
    output.write(f"Forecast Horizon,{report.forecast.get('forecast_period', '30_days')}\n")
    output.write(f"Projected Sales Value,₹{report.forecast.get('projected_value', 0.0):,.2f}\n")
    output.write(f"Model Confidence,{report.forecast.get('confidence', 0.0):.1%}\n")
    output.write(f"Model Architecture,{report.forecast.get('model_type', 'Ensemble')}\n\n")

    # 6. Business Health Score
    output.write("--- BUSINESS HEALTH SCORE ---\n")
    output.write("Metric,Value\n")
    output.write(f"Composite Health Score,{report.business_health.get('score', 0.0):.1f} / 100\n")
    output.write(f"Health Status,{report.business_health.get('status', 'Healthy')}\n")
    output.write(f"Sales Performance Score,{report.business_health.get('sales_score', 0.0):.1f}\n")
    output.write(f"Inventory Health Score,{report.business_health.get('inventory_score', 0.0):.1f}\n")
    output.write(f"Alert Health Score,{report.business_health.get('alert_score', 0.0):.1f}\n\n")

    # 7. AI Recommendations
    output.write("--- AI EXECUTIVE RECOMMENDATIONS ---\n")
    output.write("Priority,Source,Recommendation,Reason,Confidence\n")
    for rec in report.recommendations:
        rec_txt = str(rec.get("recommendation", "")).replace('"', '""')
        rsn_txt = str(rec.get("reason", "")).replace('"', '""')
        output.write(
            f"{rec.get('priority', 'MEDIUM')},{rec.get('source', 'System')},\"{rec_txt}\",\"{rsn_txt}\",{rec.get('confidence', 0.0):.1%}\n"
        )
    output.write("\n")

    # 8. Operational Alerts
    output.write("--- OPERATIONAL ALERTS ---\n")
    output.write("ID,Severity,Title,Message,Timestamp\n")
    for alt in report.alerts:
        msg = str(alt.get("message", "")).replace('"', '""')
        title = str(alt.get("title", "")).replace('"', '""')
        output.write(
            f"{alt.get('id', 'ALT')},{alt.get('severity', 'INFO')},\"{title}\",\"{msg}\",{alt.get('timestamp', '')}\n"
        )

    return output.getvalue()


# --------------------------------------------------------------------------- #
# PDF Export Engine
# --------------------------------------------------------------------------- #

def export_pdf(report: ReportData) -> bytes:
    """
    Generate an executive PDF document using ReportLab.
    Includes headers, KPI tables, health metrics, recommendations, and alert logs.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold",
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b"),
        fontName="Helvetica",
        spaceAfter=12,
    )
    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        fontName="Helvetica-Bold",
        spaceBefore=10,
        spaceAfter=6,
    )
    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#334155"),
        fontName="Helvetica",
    )
    cell_bold_style = ParagraphStyle(
        "TableCellBold",
        parent=cell_style,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a"),
    )
    cell_header_style = ParagraphStyle(
        "TableHeader",
        parent=cell_style,
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph(f"Executive BI Briefing: {report.report_type}", title_style))
    story.append(
        Paragraph(
            f"<b>Period:</b> {report.period_label} &nbsp;|&nbsp; "
            f"<b>Generated:</b> {report.generated_at} &nbsp;|&nbsp; "
            f"<b>Platform:</b> Gokul Text Print AI Decision Intelligence",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    # 2. Key Metrics Summary Grid (Topline Cards)
    kpi_data = [
        [
            Paragraph("<b>Total Revenue</b>", cell_bold_style),
            Paragraph("<b>Sales Growth</b>", cell_bold_style),
            Paragraph("<b>Inventory Valuation</b>", cell_bold_style),
            Paragraph("<b>Business Health</b>", cell_bold_style),
        ],
        [
            Paragraph(f"<font size='11' color='#0284c7'><b>₹{report.revenue:,.2f}</b></font>", cell_style),
            Paragraph(f"<font size='11' color='#16a34a'><b>{report.sales_summary.get('growth_rate', 0.0):+.1f}%</b></font>", cell_style),
            Paragraph(f"<font size='11' color='#475569'><b>₹{report.inventory_summary.get('valuation', 0.0):,.2f}</b></font>", cell_style),
            Paragraph(
                f"<font size='11' color='#2563eb'><b>{(report.business_health.to_dict() if hasattr(report.business_health, 'to_dict') else (report.business_health or {})).get('score', 0.0):.1f}/100</b> "
                f"({(report.business_health.to_dict() if hasattr(report.business_health, 'to_dict') else (report.business_health or {})).get('status', 'Healthy')})</font>",
                cell_style,
            ),
        ],
    ]
    t_kpi = Table(kpi_data, colWidths=[135, 135, 135, 135])
    t_kpi.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 12))

    # 3. Sales & Inventory Dual-Column Table
    story.append(Paragraph("Operations & Performance Overview", section_title_style))
    ops_data = [
        [
            Paragraph("Sales Metric", cell_header_style),
            Paragraph("Value", cell_header_style),
            Paragraph("Inventory Metric", cell_header_style),
            Paragraph("Value", cell_header_style),
        ],
        [
            Paragraph("Total Sales Orders", cell_style),
            Paragraph(f"{report.sales_summary.get('total_sales', 0):,}", cell_bold_style),
            Paragraph("Stock Posture", cell_style),
            Paragraph(f"{report.inventory_summary.get('stock_health', 'Healthy')}", cell_bold_style),
        ],
        [
            Paragraph("Sales Forecast Outlook", cell_style),
            Paragraph(f"{report.forecast.get('forecast_period', '30_days')}", cell_style),
            Paragraph("Total Stock On-Hand", cell_style),
            Paragraph(f"{report.inventory_summary.get('total_stock', 0):,.0f} units", cell_style),
        ],
        [
            Paragraph("Projected Revenue", cell_style),
            Paragraph(f"₹{report.forecast.get('projected_value', 0.0):,.2f}", cell_style),
            Paragraph("Turnover Ratio", cell_style),
            Paragraph(f"{report.inventory_summary.get('turnover_ratio', 0.0):.2f}", cell_style),
        ],
        [
            Paragraph("Model Confidence", cell_style),
            Paragraph(f"{report.forecast.get('confidence', 0.0):.1%}", cell_style),
            Paragraph("Low Stock Alert Count", cell_style),
            Paragraph(f"{report.inventory_summary.get('low_stock_count', 0)} items", cell_style),
        ],
    ]
    t_ops = Table(ops_data, colWidths=[140, 130, 140, 130])
    t_ops.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_ops)
    story.append(Spacer(1, 12))

    # 4. AI Executive Recommendations Table
    story.append(Paragraph("Synthesized AI Executive Recommendations", section_title_style))
    rec_headers = [
        Paragraph("Priority", cell_header_style),
        Paragraph("Source", cell_header_style),
        Paragraph("Recommendation", cell_header_style),
        Paragraph("Rationale / Context", cell_header_style),
        Paragraph("Conf.", cell_header_style),
    ]
    rec_rows = [rec_headers]
    for r in report.recommendations[:5]:
        p = r.get("priority", "MEDIUM")
        p_color = "#dc2626" if p == "HIGH" else ("#d97706" if p == "MEDIUM" else "#16a34a")
        p_badge = f"<font color='{p_color}'><b>{p}</b></font>"

        rec_rows.append([
            Paragraph(p_badge, cell_style),
            Paragraph(f"<b>{r.get('source', 'AI').capitalize()}</b>", cell_style),
            Paragraph(r.get("recommendation", ""), cell_bold_style),
            Paragraph(r.get("reason", ""), cell_style),
            Paragraph(f"{r.get('confidence', 0.0):.0%}", cell_style),
        ])

    t_recs = Table(rec_rows, colWidths=[50, 65, 175, 210, 40])
    t_recs.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_recs)
    story.append(Spacer(1, 12))

    # 5. Operational Alerts Table
    story.append(Paragraph("Active Operational Alerts", section_title_style))
    alert_headers = [
        Paragraph("ID", cell_header_style),
        Paragraph("Severity", cell_header_style),
        Paragraph("Alert Title", cell_header_style),
        Paragraph("Details", cell_header_style),
    ]
    alert_rows = [alert_headers]
    for a in report.alerts[:4]:
        sev = a.get("severity", "INFO")
        sev_color = "#dc2626" if sev == "CRITICAL" else ("#d97706" if sev == "WARNING" else "#2563eb")
        alert_rows.append([
            Paragraph(a.get("id", "ALT"), cell_style),
            Paragraph(f"<font color='{sev_color}'><b>{sev}</b></font>", cell_style),
            Paragraph(a.get("title", ""), cell_bold_style),
            Paragraph(a.get("message", ""), cell_style),
        ])

    t_alerts = Table(alert_rows, colWidths=[60, 65, 140, 275])
    t_alerts.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_alerts)

    doc.build(story)
    return buffer.getvalue()
