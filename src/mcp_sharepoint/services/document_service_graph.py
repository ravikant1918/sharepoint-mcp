"""Document CRUD operations using Microsoft Graph API."""
from __future__ import annotations

import base64
import io
import logging
import os
import posixpath
import tempfile
from typing import Any
from urllib.parse import quote

from ..config import get_settings
from ..core import get_sp_context
from ..utils.parsers import detect_file_type, parse_excel, parse_pdf, parse_word
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
    """Build a Graph API drive-item endpoint.

    Handles the root-vs-nested difference automatically:
      path=""          → sites/{id}/drive/root/children
      path="Reports"   → sites/{id}/drive/root:/Reports:/children

    *suffix* examples: ":/children", "", ":/content"
    """
    if path:
        return f"sites/{site_id}/drive/root:/{quote(path)}{suffix}"
    return f"sites/{site_id}/drive/root{suffix.lstrip(':')}"


def _get_drive_item_path(folder_name: str, file_name: str | None = None) -> str:
    """Get the Graph API path for a drive item."""
    client = get_sp_context()
    site_id = client._get_site_id()
    
    base_path = _normalize_path(folder_name)
    if file_name:
        base_path = f"{base_path}/{file_name}" if base_path else file_name
    
    return _drive_item_url(site_id, base_path)


@sp_retry
def list_documents(folder_name: str) -> list[dict[str, Any]]:
    """List all files in *folder_name*."""
    logger.info("Listing documents in '%s'", folder_name)
    client = get_sp_context()
    site_id = client._get_site_id()
    
    folder_path = _normalize_path(folder_name)
    
    # Get folder children
    endpoint = _drive_item_url(site_id, folder_path, ":/children")
    response = client.get(endpoint)
    
    items = response.get("value", [])
    
    # Filter only files (not folders)
    files = [item for item in items if "file" in item]
    
    return [
        {
            "name": f.get("name"),
            "url": f.get("webUrl"),
            "size": f.get("size"),
            "created": f.get("createdDateTime"),
            "modified": f.get("lastModifiedDateTime"),
            "id": f.get("id"),
        }
        for f in files
    ]


@sp_retry
def search_documents(query_text: str, row_limit: int = 20) -> list[dict[str, Any]]:
    """Search SharePoint documents using query text."""
    logger.info("Searching SharePoint documents with query '%s'", query_text)
    client = get_sp_context()
    site_id = client._get_site_id()
    
    # Use Graph API search
    endpoint = f"sites/{site_id}/drive/root/search(q='{query_text}')"
    params = {"$top": row_limit}
    response = client.get(endpoint, params=params)
    
    items = response.get("value", [])
    
    results = []
    for item in items:
        if "file" in item:  # Only files, not folders
            results.append({
                "Title": item.get("name"),
                "Path": item.get("webUrl"),
                "FileExtension": item.get("name", "").split(".")[-1] if "." in item.get("name", "") else "",
                "ServerRelativeUrl": item.get("webUrl"),
                "id": item.get("id"),
            })
    
    return results


@sp_retry
def get_document_content(
    folder_name: str, file_name: str,
) -> dict[str, Any]:
    """Download and decode a file, returning its content."""
    client = get_sp_context()
    site_id = client._get_site_id()
    
    # Get file metadata first
    folder_path = _normalize_path(folder_name)
    file_path = f"{folder_path}/{file_name}" if folder_path else file_name
    
    # Get file metadata
    metadata_endpoint = _drive_item_url(site_id, file_path)
    metadata = client.get(metadata_endpoint)
    
    file_id = metadata.get("id")
    file_size = metadata.get("size", 0)
    
    logger.info(
        "File '%s' exists=True size=%s",
        file_name, file_size,
    )

    # Download file content
    content_endpoint = f"sites/{site_id}/drive/items/{file_id}/content"
    content_bytes = client.download(content_endpoint)

    file_type = detect_file_type(file_name)

    if file_type == "pdf":
        try:
            text, pages = parse_pdf(content_bytes)
            return {
                "name": file_name,
                "content_type": "text",
                "content": text,
                "original_type": "pdf",
                "page_count": pages,
                "size": len(content_bytes),
            }
        except Exception as exc:
            logger.warning("PDF parse failed: %s", exc)

    elif file_type == "excel":
        try:
            text, sheets = parse_excel(content_bytes)
            return {
                "name": file_name,
                "content_type": "text",
                "content": text,
                "original_type": "excel",
                "sheet_count": sheets,
                "size": len(content_bytes),
            }
        except Exception as exc:
            logger.warning("Excel parse failed: %s", exc)

    elif file_type == "word":
        try:
            text, paragraphs = parse_word(content_bytes)
            return {
                "name": file_name,
                "content_type": "text",
                "content": text,
                "original_type": "word",
                "paragraph_count": paragraphs,
                "size": len(content_bytes),
            }
        except Exception as exc:
            logger.warning("Word parse failed: %s", exc)

    elif file_type == "text":
        try:
            return {
                "name": file_name,
                "content_type": "text",
                "content": content_bytes.decode("utf-8"),
                "size": len(content_bytes),
            }
        except UnicodeDecodeError:
            pass

    # Fallback: return as base64 binary
    return {
        "name": file_name,
        "content_type": "binary",
        "content_base64": base64.b64encode(content_bytes).decode(),
        "size": len(content_bytes),
    }


@sp_retry
def upload_document(
    folder_name: str,
    file_name: str,
    content: str,
    is_base64: bool = False,
) -> dict[str, Any]:
    """Upload *file_name* with *content* to *folder_name*."""
    client = get_sp_context()
    site_id = client._get_site_id()
    
    logger.info("Uploading '%s' to '%s'", file_name, folder_name)
    
    file_bytes = (
        base64.b64decode(content) if is_base64
        else content.encode("utf-8")
    )
    
    folder_path = _normalize_path(folder_name)
    file_path = f"{folder_path}/{file_name}" if folder_path else file_name
    
    # Upload file
    endpoint = _drive_item_url(site_id, file_path, ":/content")
    uploaded = client.upload(endpoint, file_bytes)
    
    return {
        "success": True,
        "message": f"File '{file_name}' uploaded successfully",
        "file": {
            "name": uploaded.get("name"),
            "url": uploaded.get("webUrl"),
            "id": uploaded.get("id"),
        },
    }


@sp_retry
def upload_from_path(
    folder_name: str,
    file_path: str,
    new_name: str | None = None,
) -> dict[str, Any]:
    """Upload a local file at *file_path* to *folder_name*."""
    dest_name = new_name or os.path.basename(file_path)
    logger.info(
        "Uploading from path '%s' as '%s'", file_path, dest_name,
    )
    
    with open(file_path, "rb") as fh:
        file_bytes = fh.read()
    
    client = get_sp_context()
    site_id = client._get_site_id()
    
    folder_path = _normalize_path(folder_name)
    dest_path = f"{folder_path}/{dest_name}" if folder_path else dest_name
    
    # Upload file
    endpoint = _drive_item_url(site_id, dest_path, ":/content")
    uploaded = client.upload(endpoint, file_bytes)
    
    return {
        "success": True,
        "message": f"File '{dest_name}' uploaded successfully",
        "file": {
            "name": uploaded.get("name"),
            "url": uploaded.get("webUrl"),
            "id": uploaded.get("id"),
        },
    }


@sp_retry
def update_document(
    folder_name: str,
    file_name: str,
    content: str,
    is_base64: bool = False,
) -> dict[str, Any]:
    """Overwrite *file_name* in *folder_name* with new *content*."""
    client = get_sp_context()
    site_id = client._get_site_id()
    
    folder_path = _normalize_path(folder_name)
    file_path = f"{folder_path}/{file_name}" if folder_path else file_name
    
    # Check if file exists
    try:
        metadata_endpoint = _drive_item_url(site_id, file_path)
        metadata = client.get(metadata_endpoint)
        file_id = metadata.get("id")
    except Exception:
        return {
            "success": False,
            "message": (
                f"File '{file_name}' does not exist "
                f"in '{folder_name}'"
            ),
        }

    file_bytes = (
        base64.b64decode(content) if is_base64
        else content.encode("utf-8")
    )
    
    # Update file content using file ID
    endpoint = f"sites/{site_id}/drive/items/{file_id}/content"
    updated = client.upload(endpoint, file_bytes)
    
    return {
        "success": True,
        "message": f"File '{file_name}' updated successfully",
        "file": {
            "name": updated.get("name"),
            "url": updated.get("webUrl"),
            "id": updated.get("id"),
        },
    }


@sp_retry
def delete_document(
    folder_name: str, file_name: str,
) -> dict[str, Any]:
    """Delete *file_name* from *folder_name*."""
    client = get_sp_context()
    site_id = client._get_site_id()
    
    folder_path = _normalize_path(folder_name)
    file_path = f"{folder_path}/{file_name}" if folder_path else file_name
    
    # Get file metadata to get ID
    try:
        metadata_endpoint = _drive_item_url(site_id, file_path)
        metadata = client.get(metadata_endpoint)
        file_id = metadata.get("id")
    except Exception:
        return {
            "success": False,
            "message": (
                f"File '{file_name}' does not exist "
                f"in '{folder_name}'"
            ),
        }

    # Delete file
    endpoint = f"sites/{site_id}/drive/items/{file_id}"
    client.delete(endpoint)
    
    return {
        "success": True,
        "message": f"File '{file_name}' deleted successfully",
    }


@sp_retry
def download_document(
    folder_name: str,
    file_name: str,
    local_path: str,
) -> dict[str, Any]:
    """Download a SharePoint file to *local_path* (fallback: system temp)."""
    client = get_sp_context()
    site_id = client._get_site_id()
    
    logger.info(
        "Downloading '%s/%s' → '%s'",
        folder_name, file_name, local_path,
    )

    folder_path = _normalize_path(folder_name)
    file_path = f"{folder_path}/{file_name}" if folder_path else file_name
    
    # Get file metadata
    try:
        metadata_endpoint = _drive_item_url(site_id, file_path)
        metadata = client.get(metadata_endpoint)
        file_id = metadata.get("id")
    except Exception:
        return {
            "success": False,
            "error": f"File '{file_name}' not found in '{folder_name}'",
        }

    # Download content
    content_endpoint = f"sites/{site_id}/drive/items/{file_id}/content"
    content_bytes = client.download(content_endpoint)

    def _save(path: str) -> dict[str, Any]:
        try:
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(path, "wb") as fh:
                fh.write(content_bytes)
            if (
                os.path.exists(path)
                and os.path.getsize(path) == len(content_bytes)
            ):
                return {
                    "success": True,
                    "path": os.path.abspath(path),
                    "size": len(content_bytes),
                }
            raise OSError("File verification failed after write")
        except Exception as exc:
            logger.error("Save failed for '%s': %s", path, exc)
            return {"success": False, "error": str(exc)}

    primary = _save(local_path)
    if primary["success"]:
        return {**primary, "method": "primary"}

    logger.warning(
        "Primary save failed (%s), trying fallback",
        primary["error"],
    )
    fallback_dir = tempfile.gettempdir()
    fallback = _save(os.path.join(fallback_dir, file_name))
    if fallback["success"]:
        return {
            **fallback,
            "method": "fallback",
            "primary_error": primary["error"],
        }

    return {
        "success": False,
        "error": "Both primary and fallback saves failed",
        "primary_error": primary["error"],
        "fallback_error": fallback["error"],
    }
