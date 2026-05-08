"""Export API endpoints."""

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
from typing import Optional

from app.exports import export_excel, export_pdf, export_png_chart
from app.services.data_service import data_store

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
