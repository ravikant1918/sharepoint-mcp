"""mcp-sharepoint — MCP Server for Microsoft SharePoint."""
import asyncio

from .server import main

__all__ = ["main"]


def run() -> None:
    """Sync entry point for the ``mcp-sharepoint`` console script."""
    asyncio.run(main())