"""Folder operations using Microsoft Graph API."""
from __future__ import annotations

import logging
import posixpath
import time
from typing import Any
from urllib.parse import quote

from ..config import get_settings
from ..core import get_sp_context
from ..utils.retry import sp_retry
from ..exceptions import SharePointConnectionError

logger = logging.getLogger(__name__)


def _normalize_path(sub_path: str | None = None) -> str:
    """Build drive-relative path from configured scope + sub_path.

    Returns empty string when both scope and sub_path are empty (= drive root).
    Graph API's drive/root already IS the document library, so NO library name
    is prepended.
    
    This function now uses the GraphClient's normalize_path method to properly
    handle SharePoint library names like "Shared Documents".
    """
    client = get_sp_context()
    scope = get_settings().shp_doc_library
    clean_path = posixpath.normpath(f"/{sub_path}").lstrip("/") if sub_path else ""
    if clean_path.startswith(".."):
        raise ValueError(f"Invalid path traversal attempt: {sub_path}")
    
    # Combine scope and path
    parts = [p for p in [scope, clean_path] if p]
    combined_path = "/".join(parts)
    
    # Use client's normalize_path if available (for Graph API)
    if hasattr(client, 'normalize_path'):
        normalized = client.normalize_path(combined_path)
        logger.debug(f"Path normalization: '{combined_path}' → '{normalized}'")
        return normalized
    
    return combined_path


def _drive_item_url(site_id: str, path: str, suffix: str = "") -> str:
    """Build a Graph API drive-item endpoint.

    Handles the root-vs-nested difference automatically:
      path=""          → sites/{id}/drive/root/children
      path="Reports"   → sites/{id}/drive/root:/Reports:/children

    *suffix* examples: ":/children", "", ":/content"
    """
    if path:
        return f"sites/{site_id}/drive/root:/{quote(path)}{suffix}"
    return f"sites/{site_id}/drive/root{suffix.lstrip(':')}"


@sp_retry
def list_folders(parent_folder: str | None = None) -> list[dict[str, Any]]:
    """List sub-folders in *parent_folder* (or library root if omitted)."""
    logger.info("Listing folders in %s", parent_folder or "root")
    client = get_sp_context()
    site_id = client._get_site_id()
    
    folder_path = _normalize_path(parent_folder)
    
    # Get folder children
    endpoint = _drive_item_url(site_id, folder_path, ":/children")
    response = client.get(endpoint)
    
    items = response.get("value", [])
    
    # Filter only folders
    folders = [item for item in items if "folder" in item]
    
    return [
        {
            "name": f.get("name"),
            "url": f.get("webUrl"),
            "created": f.get("createdDateTime"),
            "modified": f.get("lastModifiedDateTime"),
        }
        for f in folders
    ]


@sp_retry
def create_folder(folder_name: str, parent_folder: str | None = None) -> dict[str, Any]:
    """Create *folder_name* inside *parent_folder* (or library root)."""
    client = get_sp_context()
    site_id = client._get_site_id()
    parent_path = _normalize_path(parent_folder)
    logger.info("Creating folder '%s' in '%s'", folder_name, parent_path)

    # Guard: folder already exists?
    existing = list_folders(parent_folder)
    if any(f["name"] == folder_name for f in existing):
        return {"success": False, "message": f"Folder '{folder_name}' already exists"}

    # Create folder
    endpoint = _drive_item_url(site_id, parent_path, ":/children")
    
    data = {
        "name": folder_name,
        "folder": {},
        "@microsoft.graph.conflictBehavior": "fail"
    }
    
    try:
        new_folder = client.post(endpoint, data)
        return {
            "success": True,
            "message": f"Folder '{folder_name}' created successfully",
            "folder": {"name": new_folder.get("name"), "url": new_folder.get("webUrl")},
        }
    except Exception as exc:
        logger.error(f"Failed to create folder: {exc}")
        return {"success": False, "message": f"Failed to create folder: {exc}"}


@sp_retry
def delete_folder(folder_path: str) -> dict[str, Any]:
    """Delete the empty folder at *folder_path*."""
    client = get_sp_context()
    site_id = client._get_site_id()
    full_path = _normalize_path(folder_path)
    logger.info("Deleting folder: %s", full_path)
    
    # Get folder to check if it exists and get its ID
    try:
        metadata_endpoint = _drive_item_url(site_id, full_path)
        metadata = client.get(metadata_endpoint)
        folder_id = metadata.get("id")
    except SharePointConnectionError as exc:
        logger.error(
            "Folder not found for deletion",
            folder_path=folder_path,
            error=str(exc)
        )
        return {"success": False, "message": f"Folder '{folder_path}' does not exist"}

    # Check if folder has children
    children_endpoint = f"sites/{site_id}/drive/items/{folder_id}/children"
    children_response = client.get(children_endpoint)
    children = children_response.get("value", [])
    
    if len(children) > 0:
        file_count = sum(1 for c in children if "file" in c)
        folder_count = sum(1 for c in children if "folder" in c)
        if file_count > 0:
            return {"success": False, "message": f"Folder contains {file_count} file(s)"}
        if folder_count > 0:
            return {"success": False, "message": f"Folder contains {folder_count} sub-folder(s)"}

    # Delete folder
    delete_endpoint = f"sites/{site_id}/drive/items/{folder_id}"
    client.delete(delete_endpoint)
    
    return {"success": True, "message": f"Folder '{folder_path}' deleted successfully"}


@sp_retry
def get_folder_tree(parent_folder: str | None = None) -> dict[str, Any]:
    """Return a recursive tree of folders and files starting at *parent_folder*."""
    cfg = get_settings()
    client = get_sp_context()
    site_id = client._get_site_id()
    root_path = _normalize_path(parent_folder)
    logger.info("Building folder tree for '%s'", parent_folder or "root")

    try:
        root_endpoint = _drive_item_url(site_id, root_path)
        root = client.get(root_endpoint)
    except Exception as exc:
        logger.error("Cannot access root folder '%s': %s", root_path, exc)
        return {
            "name": root_path.split("/")[-1],
            "path": root_path,
            "type": "folder",
            "error": "Could not access folder",
            "children": [],
        }

    tree_nodes: dict[str, list] = {}
    pending = [parent_folder or ""]

    for level in range(cfg.shp_max_depth):
        if not pending:
            break
        logger.info("Tree level %d: %d folder(s)", level + 1, len(pending))
        current, pending = pending.copy(), []

        while current:
            batch, current = (
                current[: cfg.shp_max_folders_per_level],
                current[cfg.shp_max_folders_per_level :],
            )
            for fp in batch:
                try:
                    folder_path = _normalize_path(fp)
                    children_endpoint = _drive_item_url(site_id, folder_path, ":/children")
                    response = client.get(children_endpoint)
                    items = response.get("value", [])
                    
                    folders = [item for item in items if "folder" in item]
                    files = [item for item in items if "file" in item]
                    
                    tree_nodes[fp] = [
                        {"name": f.get("name"), "type": "folder", "children": []} 
                        for f in folders
                    ] + [
                        {
                            "name": f.get("name"),
                            "path": f.get("webUrl"),
                            "type": "file",
                            "size": f.get("size"),
                            "created": f.get("createdDateTime"),
                            "modified": f.get("lastModifiedDateTime"),
                        }
                        for f in files
                    ]
                    pending.extend(
                        f"{fp}/{f.get('name')}".strip("/") for f in folders
                    )
                except SharePointConnectionError as exc:
                    logger.warning(
                        "Failed to process folder in tree traversal",
                        folder_path=fp,
                        error=str(exc),
                        error_type=type(exc).__name__
                    )
            if current:
                time.sleep(0.1)

        if level < cfg.shp_max_depth - 1:
            time.sleep(cfg.shp_level_delay)

    def _build(path: str) -> list[dict]:
        children = tree_nodes.get(path, [])
        for child in children:
            if child["type"] == "folder":
                child["children"] = _build(f"{path}/{child['name']}".strip("/"))
        return children

    return {
        "name": root.get("name"),
        "path": root.get("webUrl"),
        "type": "folder",
        "created": root.get("createdDateTime"),
        "modified": root.get("lastModifiedDateTime"),
        "children": _build(parent_folder or ""),
    }
