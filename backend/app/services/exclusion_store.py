"""Persistent exclusion list for PAT IDs and Feedback IDs."""

import json
from pathlib import Path
from app.config import settings
from app.utils import get_logger

logger = get_logger(__name__)

EXCLUSION_FILE = settings.LOG_DIR / "exclusion_list.json"


class ExclusionStore:
    def __init__(self):
        self._data: dict = self._load()

    def _load(self) -> dict:
        if EXCLUSION_FILE.exists():
            try:
                return json.loads(EXCLUSION_FILE.read_text())
            except Exception:
                return {"pat_ids": [], "feedback_ids": []}
        return {"pat_ids": [], "feedback_ids": []}

    def _save(self):
        EXCLUSION_FILE.write_text(json.dumps(self._data, indent=2))

    def add_pat_ids(self, ids: list[str]):
        for i in ids:
            if i not in self._data["pat_ids"]:
                self._data["pat_ids"].append(i)
        self._save()
        logger.info(f"Added PAT exclusions: {ids}")

    def remove_pat_ids(self, ids: list[str]):
        self._data["pat_ids"] = [i for i in self._data["pat_ids"] if i not in ids]
        self._save()

    def add_feedback_ids(self, ids: list[str]):
        for i in ids:
            if i not in self._data["feedback_ids"]:
                self._data["feedback_ids"].append(i)
        self._save()
        logger.info(f"Added Feedback exclusions: {ids}")

    def remove_feedback_ids(self, ids: list[str]):
        self._data["feedback_ids"] = [i for i in self._data["feedback_ids"] if i not in ids]
        self._save()

    def get_pat_ids(self) -> list[str]:
        return self._data["pat_ids"]

    def get_feedback_ids(self) -> list[str]:
        return self._data["feedback_ids"]

    def get_all(self) -> dict:
        return self._data


exclusion_store = ExclusionStore()
