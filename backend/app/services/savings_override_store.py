"""Persistent savings overrides: update Reuse Saving, Automation Saving for specific Feedback IDs."""

import json
from pathlib import Path
from app.config import settings
from app.utils import get_logger

logger = get_logger(__name__)

OVERRIDES_FILE = settings.LOG_DIR / "savings_overrides.json"


class SavingsOverrideStore:
    """Stores overrides keyed by Feedback Id (from Download/Savings dataset).
    Each override: {"feedback_id": str, "reuse_saving": float, "automation_saving": float}
    """

    def __init__(self):
        self._data: dict[str, dict] = self._load()

    def _load(self) -> dict:
        if OVERRIDES_FILE.exists():
            try:
                return json.loads(OVERRIDES_FILE.read_text())
            except Exception:
                return {}
        return {}

    def _save(self):
        OVERRIDES_FILE.write_text(json.dumps(self._data, indent=2))

    def set_override(self, feedback_id: str, reuse_saving: float, automation_saving: float):
        self._data[feedback_id] = {
            "reuse_saving": reuse_saving,
            "automation_saving": automation_saving,
            "total_saving": reuse_saving + automation_saving,
        }
        self._save()
        logger.info(f"Savings override set: {feedback_id} -> reuse={reuse_saving}, auto={automation_saving}")

    def remove_override(self, feedback_id: str):
        if feedback_id in self._data:
            del self._data[feedback_id]
            self._save()

    def get_overrides(self) -> dict[str, dict]:
        return self._data

    def get_all_list(self) -> list[dict]:
        return [{"feedback_id": k, **v} for k, v in self._data.items()]


savings_override_store = SavingsOverrideStore()
