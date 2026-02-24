"""MCP server entry point and shared FastMCP instance.

Supports three transport modes (set via TRANSPORT env var):
  stdio  — default, works with Claude Desktop, Cursor, MCP Inspector
  sse    — Server-Sent Events, for HTTP-based agents
  http   — streamable-http, for remote/Docker deployments
"""
from __future__ import annotations

import asyncio
import logging as _logging
import os

import structlog
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load .env before any os.getenv() calls at module level
load_dotenv()

# ---------------------------------------------------------------------------
# Structured logging setup
# ---------------------------------------------------------------------------
_LOG_FORMAT = os.getenv("LOG_FORMAT", "console").lower()  # "console" | "json"
_LOG_LEVEL  = os.getenv("LOG_LEVEL", "INFO").upper()

_logging.basicConfig(
    level=getattr(_logging, _LOG_LEVEL, _logging.INFO),
    format="%(message)s",
)

_renderer = (
    structlog.processors.JSONRenderer()
    if _LOG_FORMAT == "json"
    else structlog.dev.ConsoleRenderer()
)

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso" if _LOG_FORMAT == "json" else "%H:%M:%S"),
        _renderer,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Read transport config from env early (needed for FastMCP constructor)
# ---------------------------------------------------------------------------
_TRANSPORT  = os.getenv("TRANSPORT", "stdio").lower()
_HTTP_HOST  = os.getenv("HTTP_HOST", "0.0.0.0")
_HTTP_PORT  = int(os.getenv("HTTP_PORT", "8000"))
_MOUNT_PATH = os.getenv("MCP_MOUNT_PATH", "/mcp")

from importlib.metadata import PackageNotFoundError, version

try:
    _VERSION = version("sharepoint-mcp")
except PackageNotFoundError:
    _VERSION = "0.0.0-dev"

# ---------------------------------------------------------------------------
# Shared FastMCP instance — host/port configured here for HTTP/SSE transports
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name="sharepoint-mcp",
    instructions=(
        "MCP Server for Microsoft SharePoint — manage folders, documents, "
        "and metadata using natural language."
    ),
    host=_HTTP_HOST,
    port=_HTTP_PORT,
)


# ---------------------------------------------------------------------------
# Health check endpoint — used by Docker, load balancers, and monitoring
# ---------------------------------------------------------------------------
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):  # noqa: ARG001
    """Return server health status as JSON."""
    from starlette.responses import JSONResponse

    return JSONResponse({
        "status": "ok",
        "version": _VERSION,
        "transport": _TRANSPORT,
        "tools": 13,
    })


async def main() -> None:
    """Validate config, register all tools, then run the MCP server."""
    logger.info("sharepoint-mcp starting", version="1.0.1", transport=_TRANSPORT)

    # Eagerly validate config — fail fast before any tool is called
    from .config import get_settings  # noqa: PLC0415
    settings = get_settings()
    logger.info("config loaded", doc_library=settings.shp_doc_library)

    # Register all tools (side-effect of importing the tool modules)
    from .tools import document_tools, folder_tools, metadata_tools  # noqa: F401, PLC0415
    logger.info("tools registered", count=13)

    # --- Transport selection ---
    if _TRANSPORT == "sse":
        logger.info("starting SSE transport", host=_HTTP_HOST, port=_HTTP_PORT, mount=_MOUNT_PATH)
        await mcp.run_sse_async(mount_path=_MOUNT_PATH)

    elif _TRANSPORT == "http":
        logger.info("starting streamable-http transport", host=_HTTP_HOST, port=_HTTP_PORT)
        await mcp.run_streamable_http_async()

    else:
        if _TRANSPORT != "stdio":
            logger.warning("unknown transport, defaulting to stdio", transport=_TRANSPORT)
        logger.info("starting stdio transport")
        await mcp.run_stdio_async()


if __name__ == "__main__":
    asyncio.run(main())