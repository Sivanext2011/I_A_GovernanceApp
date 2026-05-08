from pydantic_settings import BaseSettings
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "Automation Savings Governance & Monetization Analytics Platform"
    VERSION: str = "1.0.0"
    APP_DEBUG: bool = False
    
    # Paths
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    EXPORT_DIR: Path = BASE_DIR / "exports"
    PHOTO_DIR: Path = BASE_DIR / "photos"
    LOG_DIR: Path = BASE_DIR / "logs"
    
    # Azure AD / Graph API
    AZURE_CLIENT_ID: str = ""
    AZURE_TENANT_ID: str = ""
    AZURE_AUTHORITY: str = ""
    GRAPH_ACCESS_TOKEN: str = ""  # Manual token from Graph Explorer
    GRAPH_API_ENDPOINT: str = "https://graph.microsoft.com/v1.0"
    GRAPH_SCOPES: list = ["User.Read", "Mail.Send", "User.ReadBasic.All"]
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        # Only read vars with this prefix from environment to avoid conflicts
        env_prefix = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.AZURE_AUTHORITY and self.AZURE_TENANT_ID:
            self.AZURE_AUTHORITY = f"https://login.microsoftonline.com/{self.AZURE_TENANT_ID}"
        for d in [self.UPLOAD_DIR, self.EXPORT_DIR, self.PHOTO_DIR, self.LOG_DIR]:
            d.mkdir(parents=True, exist_ok=True)

settings = Settings()
