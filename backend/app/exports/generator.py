"""Export service: generates Excel, PDF, and PNG exports."""

import io
from pathlib import Path
from datetime import datetime
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.config import settings
from app.analytics import compute_kpis, compute_leaderboard, compute_monthly_trend
from app.utils import get_logger

logger = get_logger(__name__)


def export_excel(months: list[str], team: str = "Overall") -> Path:
    from app.services.data_service import data_store
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = settings.EXPORT_DIR / f"report_{team}_{timestamp}.xlsx"

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        # KPI Summary
        kpis = compute_kpis(months, team)
        kpi_df = pd.DataFrame([kpis])
        kpi_df.to_excel(writer, sheet_name="KPI Summary", index=False)

        # Leaderboard
        lb = compute_leaderboard(months, team, top_n=10)
        if lb:
            pd.DataFrame(lb).to_excel(writer, sheet_name="Leaderboard", index=False)

        # Monthly Trend
        trend = compute_monthly_trend(team)
        trend_df = pd.DataFrame({"Month": trend["months"], **trend["series"]})
        trend_df.to_excel(writer, sheet_name="Monthly Trend", index=False)

        # Raw filtered data
        if data_store.savings is not None:
            sav = data_store.savings
            if months:
                sav = sav[sav["CanonicalMonth"].isin(months)]
            if team != "Overall":
                sav = sav[sav["Department"] == team]
            sav.to_excel(writer, sheet_name="Savings Data", index=False)

    # Style the workbook
    _style_excel(filepath)
    logger.info(f"Excel exported: {filepath}")
    return filepath


def _style_excel(filepath: Path):
    from openpyxl import load_workbook
    wb = load_workbook(filepath)
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )
    for ws in wb.worksheets:
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=ws.max_column):
            for cell in row:
                cell.border = thin_border
        for col in ws.columns:
            max_len = max(len(str(c.value or "")) for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)
    wb.save(filepath)


def export_pdf(months: list[str], team: str = "Overall") -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = settings.EXPORT_DIR / f"report_{team}_{timestamp}.pdf"

    doc = SimpleDocTemplate(str(filepath), pagesize=landscape(A4),
                            rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=18, textColor=colors.HexColor("#1F4E79"))
    elements = []

    # Title
    elements.append(Paragraph("Automation Savings Governance Report", title_style))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Team: {team} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # KPI Table
    kpis = compute_kpis(months, team)
    kpi_data = [["Metric", "Value"]]
    kpi_data.append(["Total Downloads", str(kpis["total_downloads"])])
    kpi_data.append(["Total Reused with Savings", str(kpis["total_reused_with_savings"])])
    kpi_data.append(["Asset Savings", f"{kpis['asset_savings']:,.2f}"])
    kpi_data.append(["Automation Savings", f"{kpis['automation_savings']:,.2f}"])
    kpi_data.append(["Total Savings", f"{kpis['total_savings']:,.2f}"])
    kpi_data.append(["Billability Hours", f"{kpis['billability_hours']:,.2f}"])
    kpi_data.append(["Savings %", f"{kpis['savings_percent']:.2f}%" if kpis["savings_percent"] else "N/A"])
    kpi_data.append(["Pending Feedback", str(kpis["pending_feedback"] or "N/A")])

    kpi_table = Table(kpi_data, colWidths=[3 * inch, 3 * inch])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F4F8")]),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 30))

    # Leaderboard
    lb = compute_leaderboard(months, team, top_n=5)
    if lb:
        elements.append(Paragraph("Top 5 Practitioners", styles["Heading2"]))
        elements.append(Spacer(1, 10))
        lb_data = [["Name", "Department", "Total Savings"]]
        for entry in lb:
            lb_data.append([entry["name"], entry["department"], f"{entry['total_savings']:,.2f}"])
        lb_table = Table(lb_data, colWidths=[3 * inch, 2.5 * inch, 2 * inch])
        lb_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E86AB")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(lb_table)

    doc.build(elements)
    logger.info(f"PDF exported: {filepath}")
    return filepath


def export_png_chart(months: list[str], team: str = "Overall", chart_type: str = "trend") -> Path:
    import plotly.graph_objects as go

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = settings.EXPORT_DIR / f"chart_{chart_type}_{team}_{timestamp}.png"

    trend = compute_monthly_trend(team)
    fig = go.Figure()

    if chart_type == "trend":
        fig.add_trace(go.Scatter(x=trend["months"], y=trend["series"]["total_savings"],
                                 mode="lines+markers", name="Total Savings",
                                 line=dict(color="#1F4E79", width=3)))
        fig.update_layout(title=f"Monthly Savings Trend - {team}",
                          xaxis_title="Month", yaxis_title="Savings")
    elif chart_type == "savings_pct":
        fig.add_trace(go.Scatter(x=trend["months"], y=trend["series"]["savings_percent"],
                                 mode="lines+markers", name="Savings %",
                                 line=dict(color="#2E86AB", width=3)))
        fig.update_layout(title=f"Savings % Trend - {team}",
                          xaxis_title="Month", yaxis_title="Savings %")

    fig.update_layout(template="plotly_white", font=dict(size=12))
    fig.write_image(str(filepath), width=1200, height=600, scale=2)
    logger.info(f"PNG exported: {filepath}")
    return filepath
