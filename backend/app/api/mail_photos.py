"""Mail and photo API endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from app.config import settings
from app.graph import graph_client
from app.models.schemas import MailRequest, PendingFeedbackMailRequest, TokenRequest
from app.services.data_service import data_store
from app.governance import get_pending_feedback
from app.utils import get_logger

router = APIRouter(prefix="/api", tags=["mail", "photos"])
logger = get_logger(__name__)


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
        body = _build_pending_feedback_html(name, items)
        previews.append({
            "signum": signum,
            "name": name,
            "email": email,
            "subject": "Action Required: Pending Feedback Overdue",
            "body": body,
            "item_count": len(items),
        })
    return {"count": len(previews), "previews": previews}


@router.post("/mail/pending-feedback/send")
async def send_pending_feedback_mail(req: PendingFeedbackMailRequest):
    """Send grouped mails: one per practitioner."""
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
        body = _build_pending_feedback_html(name, items)
        success = graph_client.send_mail("Action Required: Pending Feedback Overdue", body, [email], True)
        results.append({"signum": signum, "name": name, "email": email, "sent": success})
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
        rows += f"<tr><td>{item['feedback_id']}</td><td>{item['asset_name']}</td><td>{item['due_date']}</td><td>{item['overdue_duration']} days</td></tr>"
    return f"""<p>Dear {name},</p>
<p>You have <strong>{len(items)}</strong> overdue feedback item(s). Please take action at your earliest convenience.</p>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-size:13px;">
<tr style="background:#1F4E79;color:white;"><th>Feedback ID</th><th>Asset Name</th><th>Due Date</th><th>Overdue</th></tr>
{rows}
</table>
<p>Best regards,<br/>Automation Governance Team</p>"""


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
