"""Core data service: loads, parses, filters, and caches all uploaded datasets."""

import pandas as pd
from pathlib import Path
from typing import Optional
from app.config import settings
from app.utils import get_logger, classify_mapping_dept, classify_savings_download_dept

logger = get_logger(__name__)


class DataStore:
    """In-memory data store for processed datasets."""

    def __init__(self):
        self.pat_raw: Optional[pd.DataFrame] = None
        self.mapping_raw: Optional[pd.DataFrame] = None
        self.savings_raw: Optional[pd.DataFrame] = None
        self.download_raw: Optional[pd.DataFrame] = None
        self.pat: Optional[pd.DataFrame] = None
        self.mapping: Optional[pd.DataFrame] = None
        self.savings: Optional[pd.DataFrame] = None
        self.download: Optional[pd.DataFrame] = None

    def load_pat(self, filepath: Path) -> dict:
        df = pd.read_excel(filepath, sheet_name="PAT Details")
        required = ["PAT ID", "Activity Name", "Start Date & Time", "End Date & Time",
                    "Activity Status", "Automation Assisted", "Department", "Practitioner"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"PAT file missing columns: {missing}")
        self.pat_raw = df
        self._process_pat()
        logger.info(f"PAT loaded: {len(self.pat)} filtered rows from {len(df)} total")
        return {"rows_loaded": len(self.pat), "columns": list(self.pat.columns)}

    def _process_pat(self):
        df = self.pat_raw.copy()
        df["Start Date & Time"] = pd.to_datetime(df["Start Date & Time"], errors="coerce")
        df["End Date & Time"] = pd.to_datetime(df["End Date & Time"], errors="coerce")
        mask = (
            (df["Automation Assisted"].str.strip().str.lower() == "yes") &
            (df["Activity Status"].str.strip().isin(["Successful", "UnSuccessful"])) &
            (df["Department"].str.contains("SL BOS Monetization", case=False, na=False))
        )
        df = df[mask].copy()
        df["CanonicalMonth"] = df["Start Date & Time"].dt.to_period("M").astype(str)
        # Apply exclusions
        from app.services.exclusion_store import exclusion_store
        excluded = exclusion_store.get_pat_ids()
        if excluded:
            df = df[~df["PAT ID"].astype(str).isin(excluded)]
        self.pat = df

    def load_mapping(self, filepath: Path) -> dict:
        df = pd.read_excel(filepath, sheet_name="Export")
        required = ["Month", "Pers.no.", "Corporate ID", "Emp Name",
                    "Ericsson Email Address", "Supervisor Personal No.",
                    "Billability Hours", "Level 6"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Mapping file missing columns: {missing}")
        self.mapping_raw = df
        self._process_mapping()
        logger.info(f"Mapping loaded: {len(self.mapping)} rows")
        return {"rows_loaded": len(self.mapping), "columns": list(self.mapping.columns)}

    def _process_mapping(self):
        df = self.mapping_raw.copy()
        df["MonthParsed"] = pd.to_datetime(df["Month"], format="%B %Y", errors="coerce")
        df["CanonicalMonth"] = df["MonthParsed"].dt.to_period("M").astype(str)
        df["Department"] = df["Level 6"].apply(classify_mapping_dept)
        df["Billability Hours"] = pd.to_numeric(df["Billability Hours"], errors="coerce").fillna(0)
        self.mapping = df

    def load_savings(self, filepath: Path) -> dict:
        df = pd.read_excel(filepath, sheet_name="Savings - Line Manager")
        required = ["Signum", "Feedback Date Month", "Automation Saving",
                    "Reuse Saving", "L4ORG", "L5ORG", "L6ORG"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Savings file missing columns: {missing}")
        self.savings_raw = df
        self._process_savings()
        logger.info(f"Savings loaded: {len(self.savings)} rows")
        return {"rows_loaded": len(self.savings), "columns": list(self.savings.columns)}

    def _process_savings(self):
        df = self.savings_raw.copy()
        df["MonthParsed"] = pd.to_datetime(df["Feedback Date Month"], format="%Y-%b", errors="coerce")
        df["CanonicalMonth"] = df["MonthParsed"].dt.to_period("M").astype(str)
        df["Department"] = df.apply(
            lambda r: classify_savings_download_dept(r.get("L4ORG"), r.get("L5ORG"), r.get("L6ORG")), axis=1
        )
        df["Automation Saving"] = pd.to_numeric(df["Automation Saving"], errors="coerce").fillna(0)
        df["Reuse Saving"] = pd.to_numeric(df["Reuse Saving"], errors="coerce").fillna(0)
        # Apply persistent overrides
        from app.services.savings_override_store import savings_override_store
        overrides = savings_override_store.get_overrides()
        if overrides and "Feedback Id" in df.columns:
            df["_fid_str"] = df["Feedback Id"].astype(str).str.strip().str.split(".").str[0]
            for fid, vals in overrides.items():
                fid_clean = str(fid).strip().split(".")[0]
                mask = df["_fid_str"] == fid_clean
                matched = mask.sum()
                if matched > 0:
                    df.loc[mask, "Reuse Saving"] = vals["reuse_saving"]
                    df.loc[mask, "Automation Saving"] = vals["automation_saving"]
                    logger.info(f"Override applied: Feedback Id {fid} -> {matched} rows updated")
                else:
                    logger.warning(f"Override not matched: Feedback Id {fid} (0 rows found)")
            df.drop(columns=["_fid_str"], inplace=True)
        df["TotalSaving"] = df["Automation Saving"] + df["Reuse Saving"]
        self.savings = df

    def load_download(self, filepath: Path) -> dict:
        df = pd.read_excel(filepath)
        required = ["Feedback Id", "Asset Registry Id", "Asset Name", "Signum",
                    "Download Date", "Due Date", "Overdue Duration", "L4ORG", "L5ORG", "L6ORG"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Download file missing columns: {missing}")
        self.download_raw = df
        self._process_download()
        logger.info(f"Download loaded: {len(self.download)} rows")
        return {"rows_loaded": len(self.download), "columns": list(self.download.columns)}

    def _process_download(self):
        df = self.download_raw.copy()
        df["DownloadDateParsed"] = pd.to_datetime(df["Download Date"], format="%d-%b-%Y", errors="coerce")
        df["CanonicalMonth"] = df["DownloadDateParsed"].dt.to_period("M").astype(str)
        df["Department"] = df.apply(
            lambda r: classify_savings_download_dept(r.get("L4ORG"), r.get("L5ORG"), r.get("L6ORG")), axis=1
        )
        df["Overdue Duration"] = pd.to_numeric(df["Overdue Duration"], errors="coerce").fillna(0)
        # Apply exclusions
        from app.services.exclusion_store import exclusion_store
        excluded = exclusion_store.get_feedback_ids()
        if excluded:
            df = df[~df["Feedback Id"].astype(str).isin(excluded)]
        self.download = df

    def get_available_months(self) -> list[str]:
        months = set()
        for df in [self.pat, self.mapping, self.savings, self.download]:
            if df is not None and "CanonicalMonth" in df.columns:
                months.update(df["CanonicalMonth"].dropna().unique())
        months.discard("NaT")
        return sorted(months)

    def get_latest_month(self) -> Optional[str]:
        months = self.get_available_months()
        return months[-1] if months else None


    def auto_load(self):
        """Auto-load any existing files from uploads directory on startup."""
        from app.config import settings
        upload_dir = settings.UPLOAD_DIR
        if not upload_dir.exists():
            return

        # Try to load each file type by finding the most recent matching file
        for filepath in sorted(upload_dir.glob("*.xlsx"), key=lambda f: f.stat().st_mtime, reverse=True):
            try:
                # Try to detect file type by reading sheet names
                xl = pd.ExcelFile(filepath)
                sheets = xl.sheet_names

                if "PAT Details" in sheets and self.pat is None:
                    self.load_pat(filepath)
                    logger.info(f"Auto-loaded PAT: {filepath.name}")
                elif "Export" in sheets and self.mapping is None:
                    self.load_mapping(filepath)
                    logger.info(f"Auto-loaded Mapping: {filepath.name}")
                elif "Savings - Line Manager" in sheets and self.savings is None:
                    self.load_savings(filepath)
                    logger.info(f"Auto-loaded Savings: {filepath.name}")
                elif self.download is None:
                    # Try as download file
                    df = pd.read_excel(filepath, nrows=0)
                    if "Feedback Id" in df.columns and "Overdue Duration" in df.columns:
                        self.load_download(filepath)
                        logger.info(f"Auto-loaded Download: {filepath.name}")
            except Exception as e:
                logger.debug(f"Skipped {filepath.name}: {e}")


# Singleton
data_store = DataStore()
