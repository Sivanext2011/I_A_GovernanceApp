from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UploadResponse(BaseModel):
    filename: str
    file_type: str
    rows_loaded: int
    columns: list[str]
    status: str = "success"


class MonthFilter(BaseModel):
    months: list[str] = []
    team: str = "Overall"


class KPIResponse(BaseModel):
    total_downloads: float = 0
    total_reused_with_savings: float = 0
    pending_feedback: Optional[float] = None
    asset_savings: float = 0
    automation_savings: float = 0
    total_savings: float = 0
    billability_hours: float = 0
    savings_percent: Optional[float] = None


class YTDKPIResponse(BaseModel):
    current: KPIResponse
    ytd: KPIResponse


class LeaderboardEntry(BaseModel):
    signum: str
    name: str
    email: str
    department: str
    total_savings: float
    reuse_saving: float
    automation_saving: float
    photo_url: Optional[str] = None


class GovernanceRecord(BaseModel):
    signum: str
    name: str
    email: str
    department: str
    pat_count: int = 0
    total_savings: float = 0
    status: str = "Non-Compliant"


class PendingFeedbackRecord(BaseModel):
    feedback_id: str
    asset_name: str
    signum: str
    name: str
    email: str
    department: str
    download_date: str
    due_date: str
    overdue_duration: int


class MailRequest(BaseModel):
    recipients: list[str]
    subject: str
    body: str
    is_html: bool = True


class PendingFeedbackMailRequest(BaseModel):
    signums: list[str] = []  # empty = all
    team: str = "Overall"


class MissingSavingsMailRequest(BaseModel):
    signums: list[str] = []  # empty = all
    team: str = "Overall"
    pat_months: list[str] = []
    savings_months: list[str] = []


class EscalateRequest(BaseModel):
    signums: list[str]
    escalation_type: str = "missing_savings"  # or "pending_feedback"


class TokenRequest(BaseModel):
    token: str


class ChartDataResponse(BaseModel):
    months: list[str]
    series: dict


class ExportRequest(BaseModel):
    export_type: str  # excel, pdf, png
    team: str = "Overall"
    months: list[str] = []
    include_charts: bool = True
    include_leaderboard: bool = True
