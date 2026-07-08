"""Export API endpoints."""

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from typing import Optional

from app.exports import export_excel, export_pdf, export_png_chart
from app.services.data_service import data_store
from app.config import settings

router = APIRouter(prefix="/api/exports", tags=["exports"])


@router.get("/excel")
async def download_excel(
    team: str = Query("Overall"),
    months: Optional[str] = Query(None)
):
    month_list = months.split(",") if months else data_store.get_available_months()
    filepath = export_excel(month_list, team)
    return FileResponse(filepath, filename=filepath.name,
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/pdf")
async def download_pdf(
    team: str = Query("Overall"),
    months: Optional[str] = Query(None)
):
    month_list = months.split(",") if months else data_store.get_available_months()
    filepath = export_pdf(month_list, team)
    return FileResponse(filepath, filename=filepath.name, media_type="application/pdf")


@router.get("/png")
async def download_png(
    team: str = Query("Overall"),
    months: Optional[str] = Query(None),
    chart_type: str = Query("trend")
):
    month_list = months.split(",") if months else data_store.get_available_months()
    filepath = export_png_chart(month_list, team, chart_type)
    return FileResponse(filepath, filename=filepath.name, media_type="image/png")


@router.get("/docs/monthly-savings-report")
async def download_monthly_savings_report():
    """Download the Monthly Savings Report Excel file, updating data from processed datasets."""
    from app.exports.docs_generator import generate_monthly_savings_report
    filepath = generate_monthly_savings_report()
    return FileResponse(
        filepath,
        filename="Monthly_Savings_Report.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/docs/asset-presentation")
async def download_asset_presentation(
    period: str = Query("monthly", description="Period: monthly, quarterly, half-yearly, year-end")
):
    """Generate and download the Asset Presentation PowerPoint for a given period."""
    valid_periods = ["monthly", "quarterly", "half-yearly", "year-end"]
    if period not in valid_periods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
        )
    from app.exports.docs_generator import generate_asset_presentation
    filepath = generate_asset_presentation(period)
    filename = f"Asset_{period.replace('-', '_').title()}.pptx"
    return FileResponse(
        filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
