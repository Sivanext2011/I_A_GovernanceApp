"""Governance logic: Missing Savings and Pending Feedback detection."""

import pandas as pd
from typing import Optional
from app.services.data_service import data_store
from app.utils import get_logger
from app.utils.departments import TEAMS

logger = get_logger(__name__)


def get_missing_savings(pat_months: list[str], savings_months: list[str], team: str = "Overall") -> list[dict]:
    """Practitioners with automation-assisted PAT but no/zero savings.
    PAT and Savings months are independent — activity may be in Jan, savings recorded in Feb."""
    if data_store.pat is None:
        return []

    pat_df = data_store.pat.copy()
    if pat_months:
        pat_df = pat_df[pat_df["CanonicalMonth"].isin(pat_months)]

    # Build email→signum lookup from mapping (PAT has emails, savings has signums)
    email_to_signum = {}
    if data_store.mapping is not None:
        valid_depts = [t for t in TEAMS if t != "Overall"]
        dept_filter = [team] if team != "Overall" else valid_depts
        mapping_filtered = data_store.mapping[data_store.mapping["Department"].isin(dept_filter)]
        # Build lookup: email (lowercase) → corporate ID (lowercase)
        for _, m in mapping_filtered.drop_duplicates(subset=["Ericsson Email Address"]).iterrows():
            email = str(m.get("Ericsson Email Address", "")).strip().lower()
            corp_id = str(m.get("Corporate ID", "")).strip().lower()
            if email:
                email_to_signum[email] = corp_id
        # Filter PAT to only practitioners whose email is in the team's mapping
        team_emails = set(email_to_signum.keys())
        pat_df = pat_df[pat_df["Practitioner"].str.strip().str.lower().isin(team_emails)]

    pat_practitioners = pat_df.groupby("Practitioner").size().reset_index(name="pat_count")

    results = []
    for _, row in pat_practitioners.iterrows():
        practitioner_email = row["Practitioner"]
        pat_count = int(row["pat_count"])

        # Resolve email to signum for savings lookup
        corp_id = email_to_signum.get(str(practitioner_email).strip().lower(), "")

        total_savings = 0.0
        if data_store.savings is not None and corp_id:
            sav = data_store.savings
            if savings_months:
                sav = sav[sav["CanonicalMonth"].isin(savings_months)]
            match = sav[sav["Signum"].str.strip().str.lower() == corp_id]
            total_savings = float(match["TotalSaving"].sum()) if not match.empty else 0.0

        if total_savings <= 0:
            name, email, dept = _enrich_practitioner_by_email(practitioner_email)
            manager_email = _get_manager_email(practitioner_email)
            # Get PAT activity details
            pat_activities = _get_pat_activities(pat_df, practitioner_email)
            results.append({
                "signum": practitioner_email,
                "name": name,
                "email": email,
                "department": dept,
                "pat_count": pat_count,
                "total_savings": total_savings,
                "status": "Non-Compliant",
                "manager_email": manager_email,
                "pat_activities": pat_activities,
            })

    return results


def get_pending_feedback(team: str = "Overall") -> list[dict]:
    """Download records with Overdue Duration > 0. No month filter — all data is current."""
    if data_store.download is None:
        return []

    df = data_store.download.copy()
    valid_depts = [t for t in TEAMS if t != "Overall"]
    df = df[df["Department"].isin(valid_depts)]
    if team != "Overall":
        df = df[df["Department"] == team]

    overdue = df[df["Overdue Duration"] > 0].copy()
    results = []
    for _, row in overdue.iterrows():
        signum = str(row.get("Signum", ""))
        name, email, dept = _enrich_practitioner(signum)
        results.append({
            "feedback_id": str(row.get("Feedback Id", "")),
            "asset_name": str(row.get("Asset Name", "")),
            "signum": signum,
            "name": name,
            "email": email,
            "department": dept if dept else str(row.get("Department", "")),
            "download_date": str(row.get("Download Date", "")),
            "due_date": str(row.get("Due Date", "")),
            "overdue_duration": int(row["Overdue Duration"]),
        })
    return results


def _enrich_practitioner(signum: str) -> tuple[str, str, str]:
    name = signum
    email = ""
    dept = ""
    if data_store.mapping is not None and not data_store.mapping.empty:
        match = data_store.mapping[
            data_store.mapping["Corporate ID"].str.strip().str.lower() == str(signum).strip().lower()
        ]
        if not match.empty:
            name = str(match.iloc[0].get("Emp Name", signum))
            email = str(match.iloc[0].get("Ericsson Email Address", ""))
            dept = str(match.iloc[0].get("Department", ""))
    return name, email, dept


def _enrich_practitioner_by_email(practitioner_email: str) -> tuple[str, str, str]:
    name = practitioner_email
    email = practitioner_email
    dept = ""
    if data_store.mapping is not None and not data_store.mapping.empty:
        match = data_store.mapping[
            data_store.mapping["Ericsson Email Address"].str.strip().str.lower() == str(practitioner_email).strip().lower()
        ]
        if not match.empty:
            name = str(match.iloc[0].get("Emp Name", practitioner_email))
            email = str(match.iloc[0].get("Ericsson Email Address", practitioner_email))
            dept = str(match.iloc[0].get("Department", ""))
    return name, email, dept


def _get_manager_email(practitioner_email: str) -> str:
    if data_store.mapping is None or data_store.mapping.empty:
        return ""
    match = data_store.mapping[
        data_store.mapping["Ericsson Email Address"].str.strip().str.lower() == str(practitioner_email).strip().lower()
    ]
    if match.empty:
        return ""
    supervisor_no = str(match.iloc[0].get("Supervisor Personal No.", "")).strip()
    if not supervisor_no:
        return ""
    mgr_match = data_store.mapping[
        data_store.mapping["Pers.no."].astype(str).str.strip() == supervisor_no
    ]
    if mgr_match.empty:
        return ""
    return str(mgr_match.iloc[0].get("Ericsson Email Address", ""))


def _get_pat_activities(pat_df: pd.DataFrame, practitioner_email: str) -> list[dict]:
    rows = pat_df[pat_df["Practitioner"].str.strip().str.lower() == str(practitioner_email).strip().lower()]
    activities = []
    for _, r in rows.iterrows():
        activities.append({
            "pat_id": str(r.get("PAT ID", "")),
            "activity_name": str(r.get("Activity Name", "")),
            "start_date": str(r.get("Start Date & Time", "")),
            "end_date": str(r.get("End Date & Time", "")),
            "status": str(r.get("Activity Status", "")),
        })
    return activities
