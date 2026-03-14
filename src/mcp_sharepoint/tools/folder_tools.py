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
from ..config import get_settings


def _get_default_folder() -> str:
    """Get the default folder based on configuration.
    
    Returns:
        Default folder path respecting SHP_DOC_LIBRARY or using empty string for Graph API.
    """
    settings = get_settings()
    
    # If user explicitly set a subfolder scope, use it
    if settings.shp_doc_library:
        return settings.shp_doc_library
    
    # For Graph API, use empty string (represents root of default drive)
    if settings.shp_api_type in ["graph", "graphql"]:
        return ""  # Empty = root of document library in Graph API
    
    # For Office365 API, use the configured library name
    return settings.shp_library_name


@mcp.tool(
    name="List_SharePoint_Folders",
    description=(
        "List all sub-folders in a SharePoint directory. "
        "Use None/null or empty string for document library root. "
        "For Graph API, the root represents the default document library."
    ),
)
async def list_folders_tool(parent_folder: str | None = None):
    """List all sub-folders in a SharePoint directory.
    
    Args:
        parent_folder: Parent folder path. None or empty string for root.
        
    Returns:
        List of folder information dictionaries.
    """
    # Convert empty string to None for consistency
    if parent_folder == "":
        parent_folder = None
    
    # If still None, use configured default
    if parent_folder is None:
        default = _get_default_folder()
        parent_folder = default if default else None
    
    return await asyncio.to_thread(_list_folders, parent_folder)


@mcp.tool(
    name="Get_SharePoint_Tree",
    description=(
        "Get a recursive tree view of folders and files "
        "starting from a SharePoint directory. "
        "Use None/null or empty string for document library root."
    ),
)
async def get_sharepoint_tree_tool(parent_folder: str | None = None):
    """Get a recursive tree view of folders and files.
    
    Args:
        parent_folder: Starting folder path. None or empty string for root.
        
    Returns:
        Tree structure of folders and files.
    """
    # Convert empty string to None for consistency
    if parent_folder == "":
        parent_folder = None
    
    # If still None, use configured default
    if parent_folder is None:
        default = _get_default_folder()
        parent_folder = default if default else None
    
    return await asyncio.to_thread(_get_folder_tree, parent_folder)


@mcp.tool(
    name="Create_Folder",
    description=(
        "Create a new folder in a SharePoint directory. "
        "Use None/null or empty string for parent_folder to create in document library root."
    ),
)
async def create_folder_tool(folder_name: str = "", parent_folder: str | None = None):
    """Create a new folder in SharePoint.
    
    Args:
        folder_name: Name of the folder to create.
        parent_folder: Parent folder path. None or empty string for root.
        
    Returns:
        Dictionary with creation status.
    """
    # Convert empty string to None for consistency
    if parent_folder == "":
        parent_folder = None
    
    # If still None, use configured default
    if parent_folder is None:
        default = _get_default_folder()
        parent_folder = default if default else None
    
    return await asyncio.to_thread(_create_folder, folder_name, parent_folder)


@mcp.tool(
    name="Delete_Folder",
    description=(
        "Delete an empty folder from SharePoint. "
        "Provide the full path to the folder to delete."
    ),
)
async def delete_folder_tool(folder_path: str = ""):
    """Delete an empty folder from SharePoint.
    
    Args:
        folder_path: Full path to the folder to delete.
        
    Returns:
        Dictionary with deletion status.
    """
    return await asyncio.to_thread(_delete_folder, folder_path)
