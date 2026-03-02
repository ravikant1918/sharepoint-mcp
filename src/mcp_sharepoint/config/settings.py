"""Application settings loaded from environment variables."""
from __future__ import annotations

import os
from functools import lru_cache

import structlog
from dotenv import load_dotenv

from ..exceptions import SharePointConfigError

load_dotenv()
logger = structlog.get_logger(__name__)


class Settings:
    """Validated application settings sourced from environment variables."""

    # --- Required ---
    shp_id_app: str
    shp_id_app_secret: str
    shp_site_url: str
    shp_tenant_id: str

    # --- SharePoint optional ---
    shp_library_name: str
    shp_doc_library: str
    shp_max_depth: int
    shp_max_folders_per_level: int
    shp_level_delay: float
    shp_api_type: str  # "office365" | "graph"

    # --- Server / transport ---
    transport: str      # "stdio" | "http"
    http_host: str
    http_port: int

    # --- Logging ---
    log_level: str
    log_format: str     # "console" | "json"

    def __init__(self) -> None:
        missing: list[str] = []

        def _require(key: str) -> str:
            val = os.getenv(key, "").strip()
            if not val:
                missing.append(key)
            return val

        self.shp_id_app = _require("SHP_ID_APP")
        self.shp_id_app_secret = _require("SHP_ID_APP_SECRET")
        self.shp_site_url = _require("SHP_SITE_URL")
        self.shp_tenant_id = _require("SHP_TENANT_ID")

        if missing:
            msg = f"Missing required environment variables: {', '.join(missing)}"
            logger.error("config_error", missing=missing)
            raise SharePointConfigError(msg)

        self.shp_library_name = os.getenv("SHP_LIBRARY_NAME", "Shared Documents")
        self.shp_doc_library = os.getenv("SHP_DOC_LIBRARY", "").strip()
        self.shp_max_depth = int(os.getenv("SHP_MAX_DEPTH", "15"))
        self.shp_max_folders_per_level = int(os.getenv("SHP_MAX_FOLDERS_PER_LEVEL", "100"))
        self.shp_level_delay = float(os.getenv("SHP_LEVEL_DELAY", "0.5"))
        self.shp_api_type = os.getenv("SHP_API_TYPE", "office365").lower()
        
        # Validate API type
        if self.shp_api_type not in ("office365", "graph", "graphql"):
            logger.warning(
                f"Invalid SHP_API_TYPE '{self.shp_api_type}', defaulting to 'office365'"
            )
            self.shp_api_type = "office365"

        self.transport = os.getenv("TRANSPORT", "stdio").lower()
        self.http_host = os.getenv("HTTP_HOST", "0.0.0.0")
        self.http_port = int(os.getenv("HTTP_PORT", "8000"))

        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_format = os.getenv("LOG_FORMAT", "console").lower()

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Settings(site={self.shp_site_url!r}, "
            f"library_name={self.shp_library_name!r}, "
            f"scope={self.shp_doc_library!r}, "
            f"api_type={self.shp_api_type!r}, "
            f"transport={self.transport!r})"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached, validated Settings instance."""
    return Settings()
