"""MCP tool registrations for file metadata operations."""
from __future__ import annotations

from ..server import mcp
from ..services.metadata_service import (
    get_file_metadata as _get_file_metadata,
    update_file_metadata as _update_file_metadata,
)


@mcp.tool(
    name="Get_File_Metadata",
    description="Retrieve all SharePoint list-item metadata fields for a document.",
)
async def get_file_metadata_tool(folder_name: str, file_name: str):
    return _get_file_metadata(folder_name, file_name)


@mcp.tool(
    name="Update_File_Metadata",
    description="Update one or more SharePoint list-item metadata fields for a document.",
)
async def update_file_metadata_tool(folder_name: str, file_name: str, metadata: dict):
    return _update_file_metadata(folder_name, file_name, metadata)
