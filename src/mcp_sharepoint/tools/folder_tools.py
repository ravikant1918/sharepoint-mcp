"""MCP tool registrations for folder operations."""
from __future__ import annotations

from typing import Optional

from ..server import mcp
from ..services.folder_service import (
    create_folder as _create_folder,
    delete_folder as _delete_folder,
    get_folder_tree as _get_folder_tree,
    list_folders as _list_folders,
)


@mcp.tool(
    name="List_SharePoint_Folders",
    description="List all sub-folders in a SharePoint directory (or library root if not specified).",
)
async def list_folders_tool(parent_folder: Optional[str] = None):
    return _list_folders(parent_folder)


@mcp.tool(
    name="Get_SharePoint_Tree",
    description="Get a recursive tree view of folders and files starting from a SharePoint directory.",
)
async def get_sharepoint_tree_tool(parent_folder: Optional[str] = None):
    return _get_folder_tree(parent_folder)


@mcp.tool(
    name="Create_Folder",
    description="Create a new folder in a SharePoint directory (or library root if not specified).",
)
async def create_folder_tool(folder_name: str, parent_folder: Optional[str] = None):
    return _create_folder(folder_name, parent_folder)


@mcp.tool(
    name="Delete_Folder",
    description="Delete an empty folder from SharePoint.",
)
async def delete_folder_tool(folder_path: str):
    return _delete_folder(folder_path)
