"""Persistent store for monthly pending feedback trend data."""

import json
from datetime import datetime
from pathlib import Path
from app.config import settings
from app.utils import get_logger

logger = get_logger(__name__)

TREND_FILE = settings.LOG_DIR / "pending_feedback_trend.json"


class PendingTrendStore:
    def __init__(self):
        self._data: dict = self._load()

    def _load(self) -> dict:
        if TREND_FILE.exists():
            try:
                return json.loads(TREND_FILE.read_text())
            except Exception:
                return {}
        return {}

    def _save(self):
        TREND_FILE.write_text(json.dumps(self._data, indent=2))

    def record(self, team: str, count: int) -> dict:
        month_key = datetime.now().strftime("%Y-%m")
        if team not in self._data:
            self._data[team] = {}
        self._data[team][month_key] = count
        self._save()
        logger.info(f"Recorded pending feedback: {team} {month_key} = {count}")
        return {"month": month_key, "count": count}

    def get_records(self, team: str) -> list[dict]:
        team_data = self._data.get(team, {})
        return [{"month": k, "count": v} for k, v in sorted(team_data.items())]


pending_trend_store = PendingTrendStore()
