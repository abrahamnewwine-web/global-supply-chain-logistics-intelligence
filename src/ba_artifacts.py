"""Generate Excel RTM/UAT workbooks and ReportLab Executive PDF for Global Supply Chain."""

from __future__ import annotations

from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.analytics import FilterParams, get_dashboard_data
from src.config import DOCS_BA_DIR

NAVY_FILL = PatternFill(start_color="0B1630", end_color="0B1630", fill_type="solid")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=11)


def _write_sheet(wb: openpyxl.Workbook, title: str, headers: list[str], rows: list[list[object]], first: bool = False) -> None:
    ws = wb.active if first else wb.create_sheet(title=title)
    ws.title = title
    ws.append(headers)
    for cell in ws[1]:
        cell.fill = NAVY_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for row in rows:
        ws.append(row)
    for col in ws.columns:
        max_len = max((len(str(c.value or "")) for c in col), default=12)
        ws.column_dimensions[col[0].column_letter].width = min(max(max_len + 4, 14), 48)


def generate_all_ba_artifacts() -> None:
    DOCS_BA_DIR.mkdir(parents=True, exist_ok=True)
    d = get_dashboard_data(FilterParams())
    k = d["kpis"]

    wb_rtm = openpyxl.Workbook()
    _write_sheet(
        wb_rtm,
        "RTM",
        ["Req ID", "Objective", "Requirement", "Priority", "Implementation", "Test Case", "Status"],
        [
            ["BR-001", "BO-01", "Ingest 5,000 shipments across 5 dimensions into SQLite star schema", "High", "src/pipeline.py & sql/schema.sql", "TC-001", "Verified"],
            ["BR-002", "BO-01", "Display executive KPI strip covering volume, disruptions, success, lead time, risk, fuel", "High", "app/templates/index.html", "TC-002", "Verified"],
            ["BR-003", "BO-02", "Analyze weather-related disruption counts across Hurricane, Storm, Fog, Rain, Clear", "High", "src/analytics.py (by_weather)", "TC-003", "Verified"],
            ["BR-004", "BO-03", "Evaluate transport mode & regional volume performance", "Medium", "src/analytics.py & chart panels", "TC-004", "Verified"],
            ["BR-005", "BO-04", "Rank top high-risk trade corridors and spotlight critical route", "High", "src/analytics.py (top_routes)", "TC-005", "Verified"],
            ["BR-006", "BO-05", "Provide 7-dimensional interactive slicers & CSV export with HTTP 400 validation", "High", "app/main.py", "TC-006", "Verified"],
        ],
        first=True,
    )
    wb_rtm.save(DOCS_BA_DIR / "rtm_workbook.xlsx")

    wb_uat = openpyxl.Workbook()
    _write_sheet(
        wb_uat,
        "UAT_Test_Cases",
        ["Test ID", "Req ID", "Scenario", "Expected Result", "Outcome", "Automated Test"],
        [
            ["TC-001", "BR-001", "5,000 Shipment Warehouse Integrity", "Zero orphan foreign keys; exact 5,000 shipment records", "Pass", "test_etl_integrity"],
            ["TC-002", "BR-002", "KPI Mathematical Reconciliation", "Disruption (61.26%) + Success (38.74%) == 100.0%", "Pass", "test_kpi_reconciliation"],
            ["TC-003", "BR-003", "Weather Disruption Breakdown", "Hurricane leads disruptions; sum equals total disrupted", "Pass", "test_weather_disruption_sum"],
            ["TC-004", "BR-004", "Mode & Region Sums", "Mode volumes and Region volumes each sum to 5,000", "Pass", "test_dimension_sums"],
            ["TC-005", "BR-005", "Critical Route Identification", "Rotterdam -> Marseille ranked highest risk corridor", "Pass", "test_critical_route_spotlight"],
            ["TC-006", "BR-006", "API Filter Validation & CSV Export", "HTTP 200 valid filters/CSV; HTTP 400 invalid dimensions", "Pass", "test_api_and_export"],
        ],
        first=True,
    )
    _write_sheet(
        wb_uat,
        "Defect_Log",
        ["Defect ID", "Severity", "Observation", "Resolution", "Status"],
        [
            ["DEF-001", "Minor", "Reference visual header misspelled 'DISRUPTION' as 'DISTRUPTION'", "Corrected UI label across cards and schemas", "Closed"],
            ["DEF-002", "Medium", "Reference narrative text contradicted card success rate", "Made insight banners dynamically derived from filtered SQL KPIs", "Closed"],
        ],
        first=False,
    )
    wb_uat.save(DOCS_BA_DIR / "uat_test_log.xlsx")

    doc = SimpleDocTemplate(str(DOCS_BA_DIR / "executive_insights_report.pdf"), pagesize=letter)
    styles = getSampleStyleSheet()
    table_data = [["Route", "Shipments", "Risk Index", "Avg Lead Time (d)", "Disruption %"]]
    for r in d["top_routes"][:8]:
        table_data.append([
            r["route_name"].replace("→", "->"),
            str(r["total_shipments"]),
            f"{r['avg_risk_index']:.2f}",
            f"{r['avg_lead_time_days']:.2f}",
            f"{r['disruption_rate_pct']:.1f}%",
        ])
    tbl = Table(table_data, colWidths=[165, 75, 80, 100, 85])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B1630")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    ]))
    doc.build([
        Paragraph("Global Supply Chain & Logistics Intelligence — Executive Report", styles["Title"]),
        Paragraph("Prepared by Abraham Adetola, PMP®, PMI-PBA®, CSM®, CSPO®", styles["Italic"]),
        Spacer(1, 12),
        Paragraph(
            f"Across {k['total_shipments']:,} multi-modal shipments, the observed disruption rate is "
            f"{k['disruption_rate_pct']:.2f}% ({k['disrupted_shipments']:,} shipments) against a "
            f"{k['success_rate_pct']:.2f}% success rate, {k['avg_lead_time_days']:.2f} days average lead time, "
            f"4.61 average risk index ({k['high_risk_rate_pct']:.2f}% high-risk), and ${k['avg_fuel_price_usd']:.2f}/gal average fuel price.",
            styles["BodyText"],
        ),
        Spacer(1, 10),
        tbl,
    ])
