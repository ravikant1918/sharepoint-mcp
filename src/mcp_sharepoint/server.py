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
from importlib.metadata import PackageNotFoundError, version

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
async def health_check(request: Any) -> Any:  # noqa: ARG001
    """Return server health status as JSON, including live SharePoint access validation.
    
    This endpoint validates live SharePoint connectivity and returns
    operational metrics suitable for load balancer health checks.
    
    Args:
        request: Starlette request object (unused, required by route signature)
    
    Returns:
        JSONResponse with fields:
            - status: "ok" | "degraded"
            - version: Package version string
            - transport: Active transport mode
            - tools: Number of registered tools
            - sharepoint: "connected" | "disconnected" | "unknown"
            - sharepoint_error (optional): Error details if connection failed
    
    Status Codes:
        200: SharePoint connectivity verified
        503: SharePoint connection failed (service degraded)
    """
    from starlette.responses import JSONResponse
    
    sp_status = "unknown"
    sp_error = None
    
    try:
        def _verify_sp() -> None:
            from .core import get_sp_context
            client = get_sp_context()
            
            # Test connection based on API type
            if client.api_type in ("graph", "graphql"):
                # For Graph/GraphQL API, try to get site ID
                client._get_site_id()
            else:
                # For Office365 API, use traditional load/execute
                client.ctx.load(client.ctx.web)
                client.ctx.execute_query()
            
        await asyncio.to_thread(_verify_sp)
        sp_status = "connected"
    except Exception as exc:
        sp_status = "disconnected"
        sp_error = str(exc)
        logger.error("SharePoint connection failed during health check", error=sp_error)

    payload = {
        "status": "ok" if sp_status == "connected" else "degraded",
        "version": _VERSION,
        "transport": _TRANSPORT,
        "tools": 14,
        "sharepoint": sp_status,
    }
    if sp_error:
        payload["sharepoint_error"] = sp_error

    return JSONResponse(
        payload, 
        status_code=200 if sp_status == "connected" else 503
    )


async def main() -> None:
    """Validate config, register all tools, then run the MCP server."""
    logger.info("sharepoint-mcp starting", version="1.0.1", transport=_TRANSPORT)

    # Eagerly validate config — fail fast before any tool is called
    from .config import get_settings  # noqa: PLC0415
    settings = get_settings()
    if settings.shp_doc_library:
        logger.info("config loaded — scoped to subfolder", library_name=settings.shp_library_name, scope=settings.shp_doc_library)
    else:
        logger.info("config loaded — full library access", library_name=settings.shp_library_name)

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