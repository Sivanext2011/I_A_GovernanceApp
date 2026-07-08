"""Generate document exports with live data from processed datasets."""

from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from app.config import settings
from app.analytics import compute_kpis
from app.services.data_service import data_store
from app.utils import get_logger

logger = get_logger(__name__)

HEADER_FONT = Font(bold=True, color="FFFFFF", size=9)
HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
TEAM_FILL = PatternFill(start_color="2E86AB", end_color="2E86AB", fill_type="solid")
THIN_BORDER = Border(
    left=Side(style="thin"), right=Side(style="thin"),
    top=Side(style="thin"), bottom=Side(style="thin"),
)

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

TEAMS_ORDER = ["Billing", "Charging", "SDC CS&DFE", "SDC Billing&MW"]


def _get_month_label(canonical: str) -> str:
    try:
        return MONTH_NAMES[int(canonical.split("-")[1]) - 1]
    except Exception:
        return canonical


def _get_year(months: list[str]) -> str:
    """Get the most recent year from available months."""
    years = set()
    for m in months:
        try:
            years.add(m.split("-")[0])
        except Exception:
            pass
    return max(years) if years else "2026"


def generate_monthly_savings_report() -> Path:
    """Generate Monthly Savings Report Excel from scratch using processed data."""
    output_path = settings.EXPORT_DIR / "Monthly_Savings_Report.xlsx"
    available_months = sorted(data_store.get_available_months())
    year = _get_year(available_months)
    all_months_canonical = [f"{year}-{str(i).zfill(2)}" for i in range(1, 13)]

    wb = Workbook()
    ws = wb.active
    ws.title = f"Monthly Data {year}"

    # ROW 1: Team group headers
    ws.cell(row=1, column=1, value="")
    ws.cell(row=1, column=2, value="")
    col = 3
    for team in TEAMS_ORDER:
        ws.merge_cells(start_row=1, start_column=col, end_row=1, end_column=col + 7)
        cell = ws.cell(row=1, column=col, value=team)
        cell.font = Font(bold=True, color="FFFFFF", size=10)
        cell.fill = TEAM_FILL
        cell.alignment = Alignment(horizontal="center")
        col += 8
    ws.merge_cells(start_row=1, start_column=col, end_row=1, end_column=col + 2)
    cell = ws.cell(row=1, column=col, value="Overall")
    cell.font = Font(bold=True, color="FFFFFF", size=10)
    cell.fill = TEAM_FILL
    cell.alignment = Alignment(horizontal="center")

    # ROW 2: Column headers
    headers = ["Month", "Monetization KPI"]
    for team in TEAMS_ORDER:
        headers += [
            f"Total Number of Assets Download - {team}",
            f"Total Number of Assets Reused with Savings - {team}",
            f"Pending Feedback - {team}",
            f"Asset Savings - {team}",
            f"Automation Savings - {team}",
            f"Total Savings - {team}",
            f"Billability Hours - {team}",
            f"{team} Savings %",
        ]
    headers += ["Total Savings - Monetization", "Billability Hours - Monetization", "Monetization Savings %"]

    for c_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=2, column=c_idx, value=h)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = THIN_BORDER

    # DATA ROWS: Jan-Dec
    for r_idx, month_canonical in enumerate(all_months_canonical, 3):
        month_label = _get_month_label(month_canonical)
        has_data = month_canonical in available_months

        ws.cell(row=r_idx, column=1, value=month_label).border = THIN_BORDER
        ws.cell(row=r_idx, column=2, value="16.00%").border = THIN_BORDER

        col = 3
        overall_total_savings = 0
        overall_billability = 0

        for team in TEAMS_ORDER:
            if has_data:
                kpis = compute_kpis([month_canonical], team)
                vals = [
                    kpis["total_downloads"] or "",
                    kpis["total_reused_with_savings"] or "",
                    kpis["pending_feedback"] or "",
                    kpis["asset_savings"] or "",
                    kpis["automation_savings"] or "",
                    kpis["total_savings"],
                    kpis["billability_hours"] or "",
                    f"{kpis['savings_percent']:.0f}%" if kpis["savings_percent"] else "0%",
                ]
                overall_total_savings += kpis["total_savings"]
                overall_billability += kpis["billability_hours"]
            else:
                vals = ["", "", "", "", "", 0, "", ""]

            for val in vals:
                cell = ws.cell(row=r_idx, column=col, value=val)
                cell.border = THIN_BORDER
                cell.alignment = Alignment(horizontal="right")
                col += 1

        # Overall columns
        if has_data:
            overall_pct = (overall_total_savings / overall_billability * 100) if overall_billability > 0 else None
            ws.cell(row=r_idx, column=col, value=round(overall_total_savings, 2)).border = THIN_BORDER
            ws.cell(row=r_idx, column=col + 1, value=round(overall_billability, 2)).border = THIN_BORDER
            ws.cell(row=r_idx, column=col + 2, value=f"{overall_pct:.2f}%" if overall_pct else "#DIV/0!").border = THIN_BORDER
        else:
            ws.cell(row=r_idx, column=col, value=0).border = THIN_BORDER
            ws.cell(row=r_idx, column=col + 1, value=0).border = THIN_BORDER
            ws.cell(row=r_idx, column=col + 2, value="#DIV/0!").border = THIN_BORDER

    # YTD ROW
    ytd_row = 15
    ws.cell(row=ytd_row, column=1, value="YTD").border = THIN_BORDER
    ws.cell(row=ytd_row, column=1).font = Font(bold=True)
    ws.cell(row=ytd_row, column=2, value="16.00%").border = THIN_BORDER

    col = 3
    ytd_overall_savings = 0
    ytd_overall_billability = 0

    for team in TEAMS_ORDER:
        kpis = compute_kpis(available_months, team) if available_months else {
            "total_downloads": 0, "total_reused_with_savings": 0, "pending_feedback": 0,
            "asset_savings": 0, "automation_savings": 0, "total_savings": 0,
            "billability_hours": 0, "savings_percent": None,
        }
        vals = [
            kpis["total_downloads"] or "",
            kpis["total_reused_with_savings"] or "",
            kpis["pending_feedback"] or "",
            kpis["asset_savings"] or "",
            kpis["automation_savings"] or "",
            kpis["total_savings"],
            kpis["billability_hours"] or "",
            f"{kpis['savings_percent']:.0f}%" if kpis["savings_percent"] else "0%",
        ]
        ytd_overall_savings += kpis["total_savings"]
        ytd_overall_billability += kpis["billability_hours"]

        for val in vals:
            cell = ws.cell(row=ytd_row, column=col, value=val)
            cell.border = THIN_BORDER
            cell.alignment = Alignment(horizontal="right")
            cell.font = Font(bold=True)
            col += 1

    ytd_pct = (ytd_overall_savings / ytd_overall_billability * 100) if ytd_overall_billability > 0 else None
    ws.cell(row=ytd_row, column=col, value=round(ytd_overall_savings, 2)).border = THIN_BORDER
    ws.cell(row=ytd_row, column=col + 1, value=round(ytd_overall_billability, 2)).border = THIN_BORDER
    ws.cell(row=ytd_row, column=col + 2, value=f"{ytd_pct:.2f}%" if ytd_pct else "0.00%").border = THIN_BORDER
    for c in range(col, col + 3):
        ws.cell(row=ytd_row, column=c).font = Font(bold=True)

    # Auto-fit columns
    from openpyxl.utils import get_column_letter
    for col_idx in range(1, ws.max_column + 1):
        max_len = 0
        for row_idx in range(1, ws.max_row + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            max_len = max(max_len, len(str(cell.value or "")))
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 2, 35)

    wb.save(output_path)
    logger.info(f"Monthly Savings Report generated: {output_path}")
    return output_path
