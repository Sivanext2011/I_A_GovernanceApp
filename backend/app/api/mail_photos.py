"""Mail and photo API endpoints."""

from fastapi import APIRouter, HTTPException, UploadFile, File as FastAPIFile
from fastapi.responses import FileResponse, Response
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from app.config import settings
from app.graph import graph_client
from app.models.schemas import MailRequest, PendingFeedbackMailRequest, MissingSavingsMailRequest, EscalateRequest, TokenRequest
from app.services.data_service import data_store
from app.governance import get_pending_feedback, get_missing_savings
from app.utils import get_logger

router = APIRouter(prefix="/api", tags=["mail", "photos"])
logger = get_logger(__name__)


@router.post("/mail/missing-savings/preview")
async def preview_missing_savings_mail(req: MissingSavingsMailRequest):
    """Preview mails for missing savings practitioners."""
    all_months = data_store.get_available_months()
    records = get_missing_savings(
        req.pat_months or all_months,
        req.savings_months or all_months,
        req.team
    )
    if req.signums:
        records = [r for r in records if r["signum"] in req.signums or r["email"] in req.signums]
    previews = []
    for rec in records:
        body = _build_missing_savings_html(rec["name"], rec.get("pat_activities", []))
        previews.append({
            "signum": rec["signum"],
            "name": rec["name"],
            "email": rec["email"],
            "manager_email": rec.get("manager_email", ""),
            "subject": "Action Required - Savings needs to be recorded in N365",
            "body": body,
            "pat_count": rec["pat_count"],
        })
    return {"count": len(previews), "previews": previews}


@router.post("/mail/missing-savings/send")
async def send_missing_savings_mail(req: MissingSavingsMailRequest):
    """Send mails to missing savings practitioners with CC to manager."""
    if not graph_client.is_authenticated():
        raise HTTPException(401, "Not authenticated")
    all_months = data_store.get_available_months()
    records = get_missing_savings(
        req.pat_months or all_months,
        req.savings_months or all_months,
        req.team
    )
    if req.signums:
        records = [r for r in records if r["signum"] in req.signums or r["email"] in req.signums]
    results = []
    for rec in records:
        email = rec["email"]
        if not email:
            results.append({"signum": rec["signum"], "name": rec["name"], "sent": False, "reason": "No email"})
            continue
        body = _build_missing_savings_html(rec["name"], rec.get("pat_activities", []))
        cc = [rec.get("manager_email", "")] if rec.get("manager_email") else []
        success = graph_client.send_mail(
            "Action Required - Savings needs to be recorded in N365",
            body, [email], True, cc=cc
        )
        results.append({"signum": rec["signum"], "name": rec["name"], "email": email, "cc": cc, "sent": success})
    return {"results": results}


@router.post("/mail/escalate")
async def escalate_to_manager(req: EscalateRequest):
    """Escalate to manager: sends mail with defaulter list from their team."""
    if not graph_client.is_authenticated():
        raise HTTPException(401, "Not authenticated")
    if data_store.mapping is None:
        raise HTTPException(400, "Mapping data not loaded")

    # Find manager info from mapping using supervisor personal no
    results = []
    # Group signums by manager
    manager_groups: dict[str, list[dict]] = {}
    for signum in req.signums:
        match = data_store.mapping[
            data_store.mapping["Corporate ID"].str.strip().str.lower() == signum.strip().lower()
        ]
        if match.empty:
            continue
        row = match.iloc[0]
        supervisor_no = str(row.get("Supervisor Personal No.", "")).strip()
        if not supervisor_no:
            continue
        if supervisor_no not in manager_groups:
            manager_groups[supervisor_no] = []
        manager_groups[supervisor_no].append({
            "signum": signum,
            "name": str(row.get("Emp Name", signum)),
            "email": str(row.get("Ericsson Email Address", "")),
        })

    for supervisor_no, members in manager_groups.items():
        # Find manager email from mapping
        mgr_match = data_store.mapping[
            data_store.mapping["Pers.no."].astype(str).str.strip() == supervisor_no
        ]
        if mgr_match.empty:
            results.append({"manager": supervisor_no, "sent": False, "reason": "Manager not found in mapping"})
            continue
        mgr_email = str(mgr_match.iloc[0].get("Ericsson Email Address", ""))
        mgr_name = str(mgr_match.iloc[0].get("Emp Name", ""))
        if not mgr_email:
            results.append({"manager": supervisor_no, "sent": False, "reason": "Manager email not found"})
            continue

        body = _build_escalation_html(mgr_name, members, req.escalation_type)
        subject = f"Escalation: Team Members with {req.escalation_type.replace('_', ' ').title()}"
        success = graph_client.send_mail(subject, body, [mgr_email], True)
        results.append({"manager": mgr_name, "manager_email": mgr_email, "members": len(members), "sent": success})

    return {"results": results}


@router.post("/photos/upload/{signum}")
async def upload_photo(signum: str, file: UploadFile = FastAPIFile(...)):
    """Upload a photo for a practitioner."""
    allowed_ext = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".jfif"}
    from pathlib import PurePath
    ext = PurePath(file.filename).suffix.lower() if file.filename else ""
    is_image = (file.content_type and file.content_type.startswith("image/")) or ext in allowed_ext
    if not is_image:
        raise HTTPException(400, "File must be an image")
    photo_path = settings.PHOTO_DIR / f"{signum}.jpg"
    contents = await file.read()
    # Convert to JPEG
    from io import BytesIO
    img = Image.open(BytesIO(contents))
    img = img.convert("RGB")
    img.thumbnail((400, 400))
    img.save(photo_path, "JPEG", quality=85)
    return {"status": "uploaded", "signum": signum, "path": str(photo_path)}


def _build_missing_savings_html(name: str, pat_activities: list[dict]) -> str:
    rows = ""
    for act in pat_activities:
        rows += f"<tr><td>{act['pat_id']}</td><td>{act['activity_name']}</td><td>{act['start_date']}</td><td>{act['end_date']}</td><td>{act['status']}</td></tr>"
    return f"""<p>Dear {name},</p>
<p>Our review indicates that you have completed the activities listed below and marked them as automation-assisted ("Yes") in PAT. However, the corresponding savings have not yet been recorded in N365.</p>
<p>Kindly update the savings in N365 at the earliest and confirm once completed.</p>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-size:13px;">
<tr style="background:#1F4E79;color:white;"><th>PAT ID</th><th>Activity Name</th><th>Start Date &amp; Time</th><th>End Date &amp; Time</th><th>Activity Status</th></tr>
{rows}
</table>
<br/>
<p>Regards,<br/>R. Siva</p>"""


def _build_escalation_html(mgr_name: str, members: list[dict], escalation_type: str) -> str:
    issue = "missing savings submissions" if escalation_type == "missing_savings" else "pending feedback (overdue)"
    rows = ""
    for m in members:
        rows += f"<tr><td>{m['name']}</td><td>{m['signum']}</td><td>{m['email']}</td></tr>"
    return f"""<p>Dear {mgr_name},</p>
<p>This is an escalation notice. The following team member(s) have <strong>{issue}</strong> that require attention:</p>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-size:13px;">
<tr style="background:#1F4E79;color:white;"><th>Name</th><th>Signum</th><th>Email</th></tr>
{rows}
</table>
<p>Please follow up with them to ensure compliance.</p>
<p>Best regards,<br/>Automation Governance Team</p>"""


@router.post("/mail/send")
async def send_mail(req: MailRequest):
    if not graph_client.is_authenticated():
        raise HTTPException(401, "Not authenticated with Microsoft Graph. Please authenticate first.")
    success = graph_client.send_mail(req.subject, req.body, req.recipients, req.is_html)
    if not success:
        raise HTTPException(500, "Failed to send mail")
    return {"status": "sent", "recipients": req.recipients}


@router.post("/mail/bulk-send")
async def bulk_send_mail(req: MailRequest):
    if not graph_client.is_authenticated():
        raise HTTPException(401, "Not authenticated")
    results = []
    for recipient in req.recipients:
        success = graph_client.send_mail(req.subject, req.body, [recipient], req.is_html)
        results.append({"email": recipient, "sent": success})
    return {"results": results}


@router.post("/mail/pending-feedback/preview")
async def preview_pending_feedback_mail(req: PendingFeedbackMailRequest):
    """Preview grouped mails: one per practitioner with table of their pending items."""
    records = get_pending_feedback(req.team)
    grouped = _group_by_practitioner(records)
    if req.signums:
        grouped = {k: v for k, v in grouped.items() if k in req.signums}
    previews = []
    for signum, items in grouped.items():
        email = items[0]["email"]
        name = items[0]["name"]
        manager_email = _get_manager_email_by_signum(signum)
        body = _build_pending_feedback_html(name, items)
        previews.append({
            "signum": signum,
            "name": name,
            "email": email,
            "manager_email": manager_email,
            "subject": "Action Required - Pending Feedback",
            "body": body,
            "item_count": len(items),
        })
    return {"count": len(previews), "previews": previews}


@router.post("/mail/pending-feedback/send")
async def send_pending_feedback_mail(req: PendingFeedbackMailRequest):
    """Send grouped mails: one per practitioner with CC to manager."""
    if not graph_client.is_authenticated():
        raise HTTPException(401, "Not authenticated with Microsoft Graph. Please authenticate first.")
    records = get_pending_feedback(req.team)
    grouped = _group_by_practitioner(records)
    if req.signums:
        grouped = {k: v for k, v in grouped.items() if k in req.signums}
    results = []
    for signum, items in grouped.items():
        email = items[0]["email"]
        name = items[0]["name"]
        if not email:
            results.append({"signum": signum, "name": name, "sent": False, "reason": "No email"})
            continue
        manager_email = _get_manager_email_by_signum(signum)
        cc = [manager_email] if manager_email else []
        body = _build_pending_feedback_html(name, items)
        success = graph_client.send_mail("Action Required - Pending Feedback", body, [email], True, cc=cc)
        results.append({"signum": signum, "name": name, "email": email, "cc": cc, "sent": success})
    return {"results": results}


def _group_by_practitioner(records: list[dict]) -> dict:
    grouped = {}
    for rec in records:
        signum = rec["signum"]
        if signum not in grouped:
            grouped[signum] = []
        grouped[signum].append(rec)
    return grouped


def _build_pending_feedback_html(name: str, items: list[dict]) -> str:
    rows = ""
    for item in items:
        rows += f"<tr><td>{item['feedback_id']}</td><td>{item.get('asset_registry_id', '')}</td><td>{item['asset_name']}</td><td>{item.get('download_date', '')}</td><td>{item['due_date']}</td><td>{item['overdue_duration']}</td></tr>"
    return f"""<p>Dear {name},</p>
<p>Below assets are pending feedback beyond due date:</p>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-size:13px;">
<tr style="background:#1F4E79;color:white;"><th>Feedback Id</th><th>Asset Registry Id</th><th>Asset Name</th><th>Download Date</th><th>Due Date</th><th>Overdue</th></tr>
{rows}
</table>
<br/>
<p>Kindly update or cancel.</p>
<p>Regards,<br/>R. Siva</p>"""


def _get_manager_email_by_signum(signum: str) -> str:
    if data_store.mapping is None or data_store.mapping.empty:
        return ""
    match = data_store.mapping[
        data_store.mapping["Corporate ID"].str.strip().str.lower() == str(signum).strip().lower()
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


@router.get("/auth/status")
async def auth_status():
    return {"authenticated": graph_client.is_authenticated()}


@router.post("/auth/device-flow")
async def start_device_flow():
    try:
        flow = graph_client.initiate_device_flow()
        return {"user_code": flow["user_code"], "verification_uri": flow["verification_uri"],
                "message": flow["message"], "flow_id": id(flow)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/auth/token")
async def set_access_token(req: TokenRequest):
    """Set Graph API access token manually (from Graph Explorer)."""
    if not req.token.strip():
        raise HTTPException(400, "Token is required")
    settings.GRAPH_ACCESS_TOKEN = req.token.strip()
    return {"status": "ok", "authenticated": graph_client.is_authenticated()}


@router.get("/photos/{signum}")
async def get_photo(signum: str):
    # Check local cache first
    photo_path = settings.PHOTO_DIR / f"{signum}.jpg"
    if photo_path.exists():
        return FileResponse(photo_path, media_type="image/jpeg")

    # Try Graph API
    if graph_client.is_authenticated() and data_store.mapping is not None:
        match = data_store.mapping[
            data_store.mapping["Corporate ID"].str.strip().str.lower() == signum.strip().lower()
        ]
        if not match.empty:
            email = match.iloc[0].get("Ericsson Email Address", "")
            if email:
                cached = graph_client.fetch_and_cache_photo(email, signum)
                if cached:
                    return FileResponse(cached, media_type="image/jpeg")

    # Generate initials avatar
    avatar = _generate_initials_avatar(signum)
    return Response(content=avatar, media_type="image/png")


def _generate_initials_avatar(signum: str) -> bytes:
    import io
    size = 200
    colors = ["#1F4E79", "#2E86AB", "#A23B72", "#F18F01", "#C73E1D"]
    bg_color = colors[hash(signum) % len(colors)]
    initials = signum[:2].upper()

    img = Image.new("RGB", (size, size), bg_color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 72)
    except (IOError, OSError):
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), initials, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - w) / 2, (size - h) / 2 - 10), initials, fill="white", font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
