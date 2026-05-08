"""Governance API endpoints."""

from fastapi import APIRouter, Query
from typing import Optional

from app.governance import get_missing_savings, get_pending_feedback
from app.services.data_service import data_store

router = APIRouter(prefix="/api/governance", tags=["governance"])


@router.get("/missing-savings")
async def missing_savings(
    team: str = Query("Overall"),
    pat_months: Optional[str] = Query(None, description="Comma-separated months for PAT filter"),
    savings_months: Optional[str] = Query(None, description="Comma-separated months for Savings filter"),
):
    all_months = data_store.get_available_months()
    pat_month_list = pat_months.split(",") if pat_months else all_months
    savings_month_list = savings_months.split(",") if savings_months else all_months
    records = get_missing_savings(pat_month_list, savings_month_list, team)
    return {"count": len(records), "records": records}


@router.get("/pending-feedback")
async def pending_feedback(
    team: str = Query("Overall"),
):
    records = get_pending_feedback(team)
    return {"count": len(records), "records": records}


@router.get("/debug-missing-savings")
async def debug_missing_savings():
    """Temporary debug endpoint."""
    from app.utils.departments import TEAMS
    pat = data_store.pat
    mapping = data_store.mapping
    info = {}
    if pat is not None:
        info["pat_rows"] = len(pat)
        info["pat_months"] = list(pat["CanonicalMonth"].unique())
        info["pat_practitioners_sample"] = list(pat["Practitioner"].head(5))
    if mapping is not None:
        valid_depts = [t for t in TEAMS if t != "Overall"]
        filtered = mapping[mapping["Department"].isin(valid_depts)]
        info["mapping_valid_dept_rows"] = len(filtered)
        info["mapping_corporate_id_sample"] = list(filtered["Corporate ID"].head(5))
        # Check overlap
        if pat is not None:
            pat_practitioners = set(pat["Practitioner"].str.lower().unique())
            mapping_ids = set(filtered["Corporate ID"].str.lower().unique())
            info["overlap_count"] = len(pat_practitioners & mapping_ids)
            info["pat_not_in_mapping"] = list(pat_practitioners - mapping_ids)[:5]
    return info
