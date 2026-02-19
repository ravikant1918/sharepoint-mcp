"""MCP server entry point and shared FastMCP instance.

Supports two transport modes (set via TRANSPORT env var):
  stdio  — default, works with Claude Desktop, Cursor, MCP Inspector
  http   — streamable-http for remote/Docker deployments
"""
from __future__ import annotations

import asyncio
import os
import sys

import structlog
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Structured logging setup
# ---------------------------------------------------------------------------
_LOG_FORMAT = os.getenv("LOG_FORMAT", "console").lower()  # "console" | "json"
_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

if _LOG_FORMAT == "json":
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
else:
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Shared FastMCP instance (imported by tools/* sub-modules)
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name="sharepoint-mcp",
    instructions=(
        "MCP Server for Microsoft SharePoint — manage folders, documents, "
        "and metadata using natural language."
    ),
)


async def main() -> None:
    """Validate config, register all tools, then run the MCP server."""
    logger.info("sharepoint-mcp starting", version="1.0.0")

    # Eagerly validate config — fail fast before any tool is called
    from .config import get_settings  # noqa: PLC0415
    settings = get_settings()
    logger.info(
        "config loaded",
        doc_library=settings.shp_doc_library,
        transport=settings.transport,
    )

    # Register all tools (side-effect of importing the tool modules)
    from .tools import document_tools, folder_tools, metadata_tools  # noqa: F401, PLC0415
    logger.info("tools registered", count=13)

    # --- Transport selection ---
    transport = settings.transport.lower()

    if transport == "http":
        logger.info(
            "starting HTTP transport",
            host=settings.http_host,
            port=settings.http_port,
        )
        await mcp.run_http_async(
            host=settings.http_host,
            port=settings.http_port,
        )
    else:
        if transport != "stdio":
            logger.warning("unknown transport, defaulting to stdio", transport=transport)
        logger.info("starting stdio transport")
        await mcp.run_stdio_async()


if __name__ == "__main__":
    asyncio.run(main())