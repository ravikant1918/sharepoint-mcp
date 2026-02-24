"""MCP tool registrations for folder operations."""
from __future__ import annotations

import asyncio

from ..server import mcp
from ..services.folder_service import (
    create_folder as _create_folder,
)
from ..services.folder_service import (
    delete_folder as _delete_folder,
)
from ..services.folder_service import (
    get_folder_tree as _get_folder_tree,
)
from ..services.folder_service import (
    list_folders as _list_folders,
)


@mcp.tool(
    name="List_SharePoint_Folders",
    description=(
        "List all sub-folders in a SharePoint directory "
        "(or library root if not specified)."
    ),
)
async def list_folders_tool(parent_folder: str | None = None):
    return await asyncio.to_thread(_list_folders, parent_folder)


@mcp.tool(
    name="Get_SharePoint_Tree",
    description=(
        "Get a recursive tree view of folders and files "
        "starting from a SharePoint directory."
    ),
)
async def get_sharepoint_tree_tool(parent_folder: str | None = None):
    return await asyncio.to_thread(_get_folder_tree, parent_folder)


@mcp.tool(
    name="Create_Folder",
    description="Create a new folder in a SharePoint directory (or library root if not specified).",
)
async def create_folder_tool(folder_name: str, parent_folder: str | None = None):
    return await asyncio.to_thread(_create_folder, folder_name, parent_folder)


@mcp.tool(
    name="Delete_Folder",
    description="Delete an empty folder from SharePoint.",
)
async def delete_folder_tool(folder_path: str):
    return await asyncio.to_thread(_delete_folder, folder_path)
