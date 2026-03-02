"""File metadata operations using Microsoft Graph API."""
from __future__ import annotations

import logging
import posixpath
from typing import Any
from urllib.parse import quote

from ..config import get_settings
from ..core import get_sp_context
from ..utils.retry import sp_retry

logger = logging.getLogger(__name__)


def _normalize_path(sub_path: str = "") -> str:
    """Build drive-relative path from configured scope + sub_path.

    Returns empty string when both scope and sub_path are empty (= drive root).
    Graph API's drive/root already IS the document library, so NO library name
    is prepended.
    """
    scope = get_settings().shp_doc_library
    clean_path = posixpath.normpath(f"/{sub_path}").lstrip("/") if sub_path else ""
    if clean_path.startswith(".."):
        raise ValueError(f"Invalid path traversal attempt: {sub_path}")
    parts = [p for p in [scope, clean_path] if p]
    return "/".join(parts)


def _drive_item_url(site_id: str, path: str, suffix: str = "") -> str:
    """Build a Graph API drive-item endpoint."""
    if path:
        return f"sites/{site_id}/drive/root:/{quote(path)}{suffix}"
    return f"sites/{site_id}/drive/root{suffix.lstrip(':')}"


@sp_retry
def get_file_metadata(folder_name: str, file_name: str) -> dict[str, Any]:
    """Return all list-item properties for *file_name*."""
    client = get_sp_context()
    site_id = client._get_site_id()
    
    folder_path = _normalize_path(folder_name)
    file_path = f"{folder_path}/{file_name}" if folder_path else file_name
    
    logger.info("Getting metadata for '%s'", file_path)

    # Get file metadata from Graph API
    endpoint = _drive_item_url(site_id, file_path)
    try:
        file_metadata = client.get(endpoint)
        
        # Get list item for SharePoint-specific metadata
        list_item_endpoint = f"sites/{site_id}/drive/items/{file_metadata.get('id')}/listItem"
        list_item = client.get(list_item_endpoint)
        
        # Get fields from list item
        fields = list_item.get("fields", {})
        
        metadata = {
            k: str(v)
            for k, v in fields.items()
            if v is not None
        }
        
        # Add standard metadata from drive item
        metadata.update({
            "id": file_metadata.get("id"),
            "name": file_metadata.get("name"),
            "size": str(file_metadata.get("size", 0)),
            "created": file_metadata.get("createdDateTime"),
            "modified": file_metadata.get("lastModifiedDateTime"),
            "webUrl": file_metadata.get("webUrl"),
        })
        
        return {
            "success": True,
            "message": f"Metadata retrieved for '{file_name}'",
            "metadata": metadata,
            "file": {"name": file_name, "path": file_path},
        }
    except Exception as exc:
        logger.error(f"Failed to get metadata: {exc}")
        return {
            "success": False,
            "message": f"Failed to retrieve metadata: {exc}",
        }


@sp_retry
def update_file_metadata(
    folder_name: str,
    file_name: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Update list-item *metadata* fields for *file_name*."""
    client = get_sp_context()
    site_id = client._get_site_id()
    
    folder_path = _normalize_path(folder_name)
    file_path = f"{folder_path}/{file_name}" if folder_path else file_name
    
    logger.info("Updating metadata for '%s'", file_path)

    try:
        # Get file ID
        file_endpoint = _drive_item_url(site_id, file_path)
        file_metadata = client.get(file_endpoint)
        file_id = file_metadata.get("id")
        
        # Prepare fields to update
        form_values: dict[str, str] = {}
        for key, value in metadata.items():
            if value is None:
                continue
            if isinstance(value, bool):
                form_values[key] = True if value else False
            elif isinstance(value, list):
                form_values[key] = value
            else:
                form_values[key] = str(value)

        if not form_values:
            return {"success": True, "message": "No fields to update"}

        # Update list item fields
        list_item_endpoint = f"sites/{site_id}/drive/items/{file_id}/listItem/fields"
        client.put(list_item_endpoint, form_values)
        
        return {
            "success": True,
            "message": f"Updated {len(form_values)} field(s) for '{file_name}'",
        }
    except Exception as exc:
        logger.error(f"Failed to update metadata: {exc}")
        return {
            "success": False,
            "message": f"Failed to update metadata: {exc}",
        }
