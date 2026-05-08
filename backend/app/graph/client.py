"""Microsoft Graph API integration: authentication, photos, mail."""

import json
import msal
import requests
from pathlib import Path
from typing import Optional
from app.config import settings
from app.utils import get_logger

logger = get_logger(__name__)

TOKEN_CACHE_FILE = settings.LOG_DIR / ".token_cache.json"


class GraphClient:
    def __init__(self):
        self._app: Optional[msal.PublicClientApplication] = None
        self._token_cache = msal.SerializableTokenCache()
        self._cache_loaded = False

    def _load_cache(self):
        if not self._cache_loaded:
            self._cache_loaded = True
            if TOKEN_CACHE_FILE.exists():
                self._token_cache.deserialize(TOKEN_CACHE_FILE.read_text())

    def _save_cache(self):
        if self._token_cache.has_state_changed:
            TOKEN_CACHE_FILE.write_text(self._token_cache.serialize())

    @property
    def app(self) -> Optional[msal.PublicClientApplication]:
        if not settings.AZURE_CLIENT_ID or settings.AZURE_CLIENT_ID == "your-client-id-here":
            return None
        if self._app is None:
            self._load_cache()
            self._app = msal.PublicClientApplication(
                settings.AZURE_CLIENT_ID,
                authority=settings.AZURE_AUTHORITY or None,
                token_cache=self._token_cache,
            )
        return self._app

    def get_token_silent(self) -> Optional[str]:
        # Use manual token from .env / Graph Explorer if provided
        if settings.GRAPH_ACCESS_TOKEN:
            return settings.GRAPH_ACCESS_TOKEN
        if not self.app:
            return None
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(settings.GRAPH_SCOPES, account=accounts[0])
            if result and "access_token" in result:
                self._save_cache()
                return result["access_token"]
        return None

    def initiate_device_flow(self) -> dict:
        if not self.app:
            raise RuntimeError("Azure AD not configured. Set AZURE_CLIENT_ID and AZURE_TENANT_ID in .env")
        flow = self.app.initiate_device_flow(scopes=settings.GRAPH_SCOPES)
        if "user_code" not in flow:
            raise RuntimeError("Failed to create device flow")
        return flow

    def acquire_token_by_device_flow(self, flow: dict) -> Optional[str]:
        if not self.app:
            return None
        result = self.app.acquire_token_by_device_flow(flow)
        if "access_token" in result:
            self._save_cache()
            return result["access_token"]
        logger.error(f"Token acquisition failed: {result.get('error_description')}")
        return None

    def is_authenticated(self) -> bool:
        return self.get_token_silent() is not None

    def get_user_photo(self, email: str) -> Optional[bytes]:
        token = self.get_token_silent()
        if not token:
            return None
        try:
            resp = requests.get(
                f"{settings.GRAPH_API_ENDPOINT}/users/{email}/photo/$value",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.content
        except Exception as e:
            logger.warning(f"Photo fetch failed for {email}: {e}")
        return None

    def fetch_and_cache_photo(self, email: str, signum: str) -> Optional[Path]:
        photo_path = settings.PHOTO_DIR / f"{signum}.jpg"
        if photo_path.exists():
            return photo_path
        data = self.get_user_photo(email)
        if data:
            photo_path.write_bytes(data)
            return photo_path
        return None

    def send_mail(self, subject: str, body: str, recipients: list[str], is_html: bool = True) -> bool:
        token = self.get_token_silent()
        if not token:
            logger.error("No token available for sending mail")
            return False
        message = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML" if is_html else "Text", "content": body},
                "toRecipients": [{"emailAddress": {"address": r}} for r in recipients],
            }
        }
        try:
            resp = requests.post(
                f"{settings.GRAPH_API_ENDPOINT}/me/sendMail",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=message,
                timeout=30,
            )
            if resp.status_code == 202:
                logger.info(f"Mail sent to {recipients}")
                return True
            logger.error(f"Mail send failed: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.error(f"Mail send error: {e}")
        return False


graph_client = GraphClient()
