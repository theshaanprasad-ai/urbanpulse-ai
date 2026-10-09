"""
Application configuration for UrbanPulse AI.
Values can be overridden through environment variables or a local `.env` file.
"""

from pathlib import Path
from typing import List
from urllib.parse import quote_plus, urlparse
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    _project_root = Path(__file__).resolve().parents[3]
    model_config = SettingsConfigDict(
        env_file=(
            _project_root / ".env",
            _project_root / "backend" / ".env",
        ),
        extra="ignore",
    )

    APP_NAME: str = "UrbanPulse AI"
    APP_SUBTITLE: str = "AI-Powered Urban Issue Intelligence and Early-Warning Platform"
    APP_VERSION: str = "2.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    # LIVE is the production path. Fixture modes are opt-in for development only.
    DATA_MODE: str = Field(default="LIVE", description="Operational data mode")
    DEFAULT_CITY: str = "chennai"
    # Seeds the synthetic Chennai demo dataset so the control room is populated on
    # a fresh database. Set false for a real deployment that ingests live records.
    SEED_DEMO_DATA: bool = True

    DATABASE_URL: str = "sqlite:///./urbanpulse.db"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_DB_URL: str = ""
    SUPABASE_DB_PASSWORD: str = ""

    # Optional providers. None are required for the demo.
    IMD_API_KEY: str = ""
    OPEN_METEO_API_KEY: str = ""
    BHUVAN_NRSC_TOKEN: str = ""
    GEMINI_API_KEY: str = ""
    # Optional MapLibre-compatible vector/terrain provider for true 3D map mode.
    MAP_TILES_TOKEN: str = ""

    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173"

    # Import guardrails
    MAX_IMPORT_BYTES: int = 5_000_000
    MAX_IMPORT_ROWS: int = 20_000

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def database_url(self) -> str:
        """Prefer an explicitly configured Supabase/Postgres connection in live deployments."""
        if self.SUPABASE_DB_URL.strip():
            return self.SUPABASE_DB_URL.strip()
        if self.SUPABASE_URL.strip() and self.SUPABASE_DB_PASSWORD:
            project_ref = urlparse(self.SUPABASE_URL).hostname.split(".")[0]
            password = quote_plus(self.SUPABASE_DB_PASSWORD)
            return f"postgresql+psycopg://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres"
        return self.DATABASE_URL

    @property
    def supabase_persistence_configured(self) -> bool:
        return bool(self.SUPABASE_URL.strip() and self.SUPABASE_DB_PASSWORD) or bool(self.SUPABASE_DB_URL.strip())


settings = Settings()
