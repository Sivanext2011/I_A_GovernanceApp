"""Analytics engine: computes KPIs, chart data, and leaderboard."""

import pandas as pd
from typing import Optional
from app.services.data_service import data_store
from app.utils import get_logger

logger = get_logger(__name__)


def _filter_by_team(df: Optional[pd.DataFrame], team: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    from app.utils.departments import TEAMS
    if team == "Overall":
        valid_depts = [t for t in TEAMS if t != "Overall"]
        return df[df["Department"].isin(valid_depts)]
    return df[df["Department"] == team]


def _filter_by_months(df: pd.DataFrame, months: list[str]) -> pd.DataFrame:
    if not months or df.empty:
        return df
    return df[df["CanonicalMonth"].isin(months)]


def compute_kpis(months: list[str], team: str = "Overall") -> dict:
    download_df = _filter_by_months(_filter_by_team(data_store.download, team), months)
    savings_df = _filter_by_months(_filter_by_team(data_store.savings, team), months)
    mapping_df = _filter_by_months(_filter_by_team(data_store.mapping, team), months)

    total_downloads = len(download_df)
    total_reused = len(savings_df)
    asset_savings = float(savings_df["Reuse Saving"].sum()) if not savings_df.empty else 0
    automation_savings = float(savings_df["Automation Saving"].sum()) if not savings_df.empty else 0
    total_savings = asset_savings + automation_savings
    billability = float(mapping_df["Billability Hours"].sum()) if not mapping_df.empty else 0
    savings_pct = (total_savings / billability * 100) if billability > 0 else None

    # Pending feedback: all data with Overdue Duration > 0 (no month filter)
    pending = 0
    all_download = _filter_by_team(data_store.download, team)
    if not all_download.empty:
        pending = int(all_download[all_download["Overdue Duration"] > 0].shape[0])

    return {
        "total_downloads": total_downloads,
        "total_reused_with_savings": total_reused,
        "pending_feedback": pending,
        "asset_savings": round(asset_savings, 2),
        "automation_savings": round(automation_savings, 2),
        "total_savings": round(total_savings, 2),
        "billability_hours": round(billability, 2),
        "savings_percent": round(savings_pct, 2) if savings_pct is not None else None,
    }


def compute_ytd_kpis(team: str = "Overall") -> dict:
    all_months = data_store.get_available_months()
    latest = data_store.get_latest_month()
    current_kpis = compute_kpis([latest] if latest else [], team)
    ytd_kpis = compute_kpis(all_months, team)
    return {"current": current_kpis, "ytd": ytd_kpis}


def compute_monthly_trend(team: str = "Overall") -> dict:
    months = sorted(data_store.get_available_months())
    savings_series = []
    automation_series = []
    reuse_series = []
    pct_series = []

    for m in months:
        kpis = compute_kpis([m], team)
        savings_series.append(kpis["total_savings"])
        automation_series.append(kpis["automation_savings"])
        reuse_series.append(kpis["asset_savings"])
        pct_series.append(kpis["savings_percent"] or 0)

    return {
        "months": months,
        "series": {
            "total_savings": savings_series,
            "automation_savings": automation_series,
            "reuse_savings": reuse_series,
            "savings_percent": pct_series,
        }
    }


def compute_department_comparison(months: list[str]) -> dict:
    from app.utils.departments import TEAMS
    teams = [t for t in TEAMS if t != "Overall"]
    result = {"teams": teams, "total_savings": [], "savings_percent": [], "downloads": []}
    for t in teams:
        kpis = compute_kpis(months, t)
        result["total_savings"].append(kpis["total_savings"])
        result["savings_percent"].append(kpis["savings_percent"] or 0)
        result["downloads"].append(kpis["total_downloads"])
    return result


def compute_downloads_vs_reuse(team: str = "Overall") -> dict:
    months = sorted(data_store.get_available_months())
    downloads = []
    reuse = []
    for m in months:
        kpis = compute_kpis([m], team)
        downloads.append(kpis["total_downloads"])
        reuse.append(kpis["total_reused_with_savings"])
    return {"months": months, "downloads": downloads, "reuse": reuse}


def compute_pending_feedback_trend(team: str = "Overall") -> dict:
    """Pending feedback = all overdue records (no month breakdown). Show total as single value."""
    all_download = _filter_by_team(data_store.download, team)
    total_pending = 0
    if not all_download.empty:
        total_pending = int(all_download[all_download["Overdue Duration"] > 0].shape[0])
    return {"months": ["Current"], "pending": [total_pending]}


def compute_leaderboard(months: list[str], team: str = "Overall", top_n: int = 5) -> list[dict]:
    savings_df = _filter_by_months(_filter_by_team(data_store.savings, team), months)
    if savings_df.empty:
        return []

    grouped = savings_df.groupby("Signum").agg(
        reuse_saving=("Reuse Saving", "sum"),
        automation_saving=("Automation Saving", "sum"),
    ).reset_index()
    grouped["total_savings"] = grouped["reuse_saving"] + grouped["automation_saving"]
    grouped = grouped.sort_values("total_savings", ascending=False).head(top_n)

    # Enrich with mapping data
    results = []
    for _, row in grouped.iterrows():
        signum = row["Signum"]
        name = signum
        email = ""
        dept = team if team != "Overall" else ""

        if data_store.mapping is not None:
            match = data_store.mapping[
                data_store.mapping["Corporate ID"].str.strip().str.lower() == str(signum).strip().lower()
            ]
            if not match.empty:
                name = match.iloc[0].get("Emp Name", signum)
                email = match.iloc[0].get("Ericsson Email Address", "")
                dept = match.iloc[0].get("Department", dept)

        results.append({
            "signum": signum,
            "name": name,
            "email": email,
            "department": dept,
            "total_savings": round(float(row["total_savings"]), 2),
            "reuse_saving": round(float(row["reuse_saving"]), 2),
            "automation_saving": round(float(row["automation_saving"]), 2),
            "photo_url": f"/api/photos/{signum}",
        })
    return results
