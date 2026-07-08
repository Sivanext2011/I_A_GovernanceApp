"""Dashboard and analytics API endpoints."""

from fastapi import APIRouter, Query
from typing import Optional

from app.analytics import (
    compute_kpis, compute_ytd_kpis, compute_monthly_trend,
    compute_department_comparison, compute_downloads_vs_reuse,
    compute_pending_feedback_trend, compute_leaderboard,
    record_pending_feedback_snapshot
)
from app.services.data_service import data_store
from app.utils.departments import TEAMS

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/months")
async def get_months():
    return {"months": data_store.get_available_months(), "latest": data_store.get_latest_month()}


@router.get("/teams")
async def get_teams():
    return {"teams": TEAMS}


@router.get("/kpis")
async def get_kpis(
    team: str = Query("Overall"),
    months: Optional[str] = Query(None, description="Comma-separated months")
):
    month_list = months.split(",") if months else data_store.get_available_months()
    return compute_kpis(month_list, team)


@router.get("/kpis/ytd")
async def get_ytd_kpis(
    team: str = Query("Overall"),
    months: Optional[str] = Query(None, description="Comma-separated months for current period")
):
    if months:
        month_list = months.split(",")
        current_kpis = compute_kpis(month_list, team)
        all_months = data_store.get_available_months()
        ytd_kpis = compute_kpis(all_months, team)
        return {"current": current_kpis, "ytd": ytd_kpis}
    return compute_ytd_kpis(team)


@router.get("/charts/monthly-trend")
async def get_monthly_trend(team: str = Query("Overall")):
    return compute_monthly_trend(team)


@router.get("/charts/department-comparison")
async def get_department_comparison(months: Optional[str] = Query(None)):
    month_list = months.split(",") if months else data_store.get_available_months()
    return compute_department_comparison(month_list)


@router.get("/charts/downloads-vs-reuse")
async def get_downloads_vs_reuse(team: str = Query("Overall")):
    return compute_downloads_vs_reuse(team)


@router.get("/charts/pending-feedback-trend")
async def get_pending_trend(team: str = Query("Overall")):
    return compute_pending_feedback_trend(team)


@router.post("/charts/pending-feedback-trend/record")
async def record_pending_trend(team: str = Query("Overall")):
    """Record current pending feedback count for this month."""
    return record_pending_feedback_snapshot(team)


@router.get("/leaderboard")
async def get_leaderboard(
    team: str = Query("Overall"),
    months: Optional[str] = Query(None),
    top_n: int = Query(5)
):
    month_list = months.split(",") if months else data_store.get_available_months()
    return compute_leaderboard(month_list, team, top_n)


@router.get("/team-stats")
async def get_team_stats(months: Optional[str] = Query(None)):
    """Get KPI stats for each team (used in Dashboard when Overall is selected)."""
    month_list = months.split(",") if months else data_store.get_available_months()
    teams = [t for t in TEAMS if t != "Overall"]
    stats = []
    for t in teams:
        kpis = compute_kpis(month_list, t)
        stats.append({"team": t, **kpis})
    return stats


@router.get("/charts/monthly-trend-all-teams")
async def get_monthly_trend_all_teams():
    """Monthly trend for all teams + overall."""
    months = sorted(data_store.get_available_months())
    result = {"months": months, "teams": {}}
    for t in TEAMS:
        savings = []
        pct = []
        for m in months:
            kpis = compute_kpis([m], t)
            savings.append(kpis["total_savings"])
            pct.append(kpis["savings_percent"] or 0)
        result["teams"][t] = {"total_savings": savings, "savings_percent": pct}
    return result
