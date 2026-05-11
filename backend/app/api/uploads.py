"""File upload API endpoints."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import shutil

from app.config import settings
from app.services.data_service import data_store
from app.utils import get_logger

router = APIRouter(prefix="/api/uploads", tags=["uploads"])
logger = get_logger(__name__)

ALLOWED_EXTENSIONS = {".xlsx", ".xls"}


def _validate_file(file: UploadFile) -> Path:
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}")
    return settings.UPLOAD_DIR / file.filename


@router.post("/pat")
async def upload_pat(file: UploadFile = File(...)):
    filepath = _validate_file(file)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        result = data_store.load_pat(filepath)
        return {"filename": file.filename, "file_type": "PAT", "status": "success", **result}
    except Exception as e:
        logger.error(f"PAT upload error: {e}")
        raise HTTPException(422, str(e))


@router.post("/mapping")
async def upload_mapping(file: UploadFile = File(...)):
    filepath = _validate_file(file)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        result = data_store.load_mapping(filepath)
        return {"filename": file.filename, "file_type": "Mapping", "status": "success", **result}
    except Exception as e:
        logger.error(f"Mapping upload error: {e}")
        raise HTTPException(422, str(e))


@router.post("/savings")
async def upload_savings(file: UploadFile = File(...)):
    filepath = _validate_file(file)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        result = data_store.load_savings(filepath)
        return {"filename": file.filename, "file_type": "Savings", "status": "success", **result}
    except Exception as e:
        logger.error(f"Savings upload error: {e}")
        raise HTTPException(422, str(e))


@router.post("/download")
async def upload_download(file: UploadFile = File(...)):
    filepath = _validate_file(file)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        result = data_store.load_download(filepath)
        return {"filename": file.filename, "file_type": "Download", "status": "success", **result}
    except Exception as e:
        logger.error(f"Download upload error: {e}")
        raise HTTPException(422, str(e))


@router.get("/status")
async def upload_status():
    return {
        "pat": data_store.pat is not None,
        "mapping": data_store.mapping is not None,
        "savings": data_store.savings is not None,
        "download": data_store.download is not None,
        "pat_rows": len(data_store.pat) if data_store.pat is not None else 0,
        "mapping_rows": len(data_store.mapping) if data_store.mapping is not None else 0,
        "savings_rows": len(data_store.savings) if data_store.savings is not None else 0,
        "download_rows": len(data_store.download) if data_store.download is not None else 0,
    }


@router.post("/exclude/pat")
async def exclude_pat_records(pat_ids: list[str]):
    """Remove specific PAT records by PAT ID."""
    if data_store.pat is None:
        raise HTTPException(400, "PAT data not loaded")
    before = len(data_store.pat)
    data_store.pat = data_store.pat[~data_store.pat["PAT ID"].astype(str).isin(pat_ids)]
    removed = before - len(data_store.pat)
    logger.info(f"Excluded {removed} PAT records")
    return {"removed": removed, "remaining": len(data_store.pat)}


@router.post("/exclude/download")
async def exclude_download_records(feedback_ids: list[str]):
    """Remove specific Download/Savings records by Feedback Id."""
    if data_store.download is None:
        raise HTTPException(400, "Download data not loaded")
    before = len(data_store.download)
    data_store.download = data_store.download[~data_store.download["Feedback Id"].astype(str).isin(feedback_ids)]
    removed = before - len(data_store.download)
    logger.info(f"Excluded {removed} Download records")
    return {"removed": removed, "remaining": len(data_store.download)}
