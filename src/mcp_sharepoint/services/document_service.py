"""Document CRUD operations against the SharePoint REST API."""
from __future__ import annotations

import base64
import io
import logging
import os
from typing import Any, Dict, List, Optional

from ..config import get_settings
from ..core import get_sp_context
from ..utils.parsers import detect_file_type, parse_pdf, parse_excel, parse_word

logger = logging.getLogger(__name__)


def _sp_path(sub_path: str = "") -> str:
    library = get_settings().shp_doc_library
    return f"{library}/{sub_path}".rstrip("/")


def list_documents(folder_name: str) -> List[Dict[str, Any]]:
    """List all files in *folder_name*."""
    logger.info("Listing documents in '%s'", folder_name)
    ctx = get_sp_context()
    folder = ctx.web.get_folder_by_server_relative_url(_sp_path(folder_name))
    files = folder.files
    ctx.load(files, ["ServerRelativeUrl", "Name", "Length", "TimeCreated", "TimeLastModified"])
    ctx.execute_query()
    return [
        {
            "name": f.name,
            "url": f.properties.get("ServerRelativeUrl"),
            "size": f.properties.get("Length"),
            "created": f.properties["TimeCreated"].isoformat() if f.properties.get("TimeCreated") else None,
            "modified": f.properties["TimeLastModified"].isoformat() if f.properties.get("TimeLastModified") else None,
        }
        for f in files
    ]


def get_document_content(folder_name: str, file_name: str) -> Dict[str, Any]:
    """Download and decode a file, returning its content in a structured dict."""
    ctx = get_sp_context()
    file_path = _sp_path(f"{folder_name}/{file_name}")
    file = ctx.web.get_file_by_server_relative_url(file_path)
    ctx.load(file, ["Exists", "Length", "Name"])
    ctx.execute_query()
    logger.info("File '%s' exists=%s size=%s", file_name, file.exists, file.length)

    buf = io.BytesIO()
    file.download(buf)
    ctx.execute_query()
    content_bytes = buf.getvalue()

    file_type = detect_file_type(file_name)

    if file_type == "pdf":
        try:
            text, pages = parse_pdf(content_bytes)
            return {"name": file_name, "content_type": "text", "content": text, "original_type": "pdf", "page_count": pages, "size": len(content_bytes)}
        except Exception as exc:
            logger.warning("PDF parse failed: %s", exc)

    elif file_type == "excel":
        try:
            text, sheets = parse_excel(content_bytes)
            return {"name": file_name, "content_type": "text", "content": text, "original_type": "excel", "sheet_count": sheets, "size": len(content_bytes)}
        except Exception as exc:
            logger.warning("Excel parse failed: %s", exc)

    elif file_type == "word":
        try:
            text, paragraphs = parse_word(content_bytes)
            return {"name": file_name, "content_type": "text", "content": text, "original_type": "word", "paragraph_count": paragraphs, "size": len(content_bytes)}
        except Exception as exc:
            logger.warning("Word parse failed: %s", exc)

    elif file_type == "text":
        try:
            return {"name": file_name, "content_type": "text", "content": content_bytes.decode("utf-8"), "size": len(content_bytes)}
        except UnicodeDecodeError:
            pass

    # Fallback: return as base64 binary
    return {"name": file_name, "content_type": "binary", "content_base64": base64.b64encode(content_bytes).decode(), "size": len(content_bytes)}


def upload_document(
    folder_name: str,
    file_name: str,
    content: str,
    is_base64: bool = False,
) -> Dict[str, Any]:
    """Upload *file_name* with *content* to *folder_name*."""
    ctx = get_sp_context()
    logger.info("Uploading '%s' to '%s'", file_name, folder_name)
    file_bytes = base64.b64decode(content) if is_base64 else content.encode("utf-8")
    folder = ctx.web.get_folder_by_server_relative_url(_sp_path(folder_name))
    uploaded = folder.upload_file(file_name, file_bytes)
    ctx.execute_query()
    return {"success": True, "message": f"File '{file_name}' uploaded successfully", "file": {"name": uploaded.name, "url": uploaded.serverRelativeUrl}}


def upload_from_path(
    folder_name: str,
    file_path: str,
    new_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Upload a local file at *file_path* to SharePoint *folder_name*."""
    ctx = get_sp_context()
    dest_name = new_name or os.path.basename(file_path)
    logger.info("Uploading from path '%s' as '%s'", file_path, dest_name)
    with open(file_path, "rb") as fh:
        file_bytes = fh.read()
    folder = ctx.web.get_folder_by_server_relative_url(_sp_path(folder_name))
    uploaded = folder.upload_file(dest_name, file_bytes)
    ctx.execute_query()
    return {"success": True, "message": f"File '{dest_name}' uploaded successfully", "file": {"name": uploaded.name, "url": uploaded.serverRelativeUrl}}


def update_document(
    folder_name: str,
    file_name: str,
    content: str,
    is_base64: bool = False,
) -> Dict[str, Any]:
    """Overwrite *file_name* in *folder_name* with new *content*."""
    ctx = get_sp_context()
    file_path = _sp_path(f"{folder_name}/{file_name}")
    file = ctx.web.get_file_by_server_relative_url(file_path)
    ctx.load(file, ["Exists", "Name", "ServerRelativeUrl"])
    ctx.execute_query()

    if not file.exists:
        return {"success": False, "message": f"File '{file_name}' does not exist in '{folder_name}'"}

    file_bytes = base64.b64decode(content) if is_base64 else content.encode("utf-8")
    folder = ctx.web.get_folder_by_server_relative_url(_sp_path(folder_name))
    updated = folder.upload_file(file_name, file_bytes)
    ctx.execute_query()
    return {"success": True, "message": f"File '{file_name}' updated successfully", "file": {"name": updated.name, "url": updated.serverRelativeUrl}}


def delete_document(folder_name: str, file_name: str) -> Dict[str, Any]:
    """Delete *file_name* from *folder_name*."""
    ctx = get_sp_context()
    file_path = _sp_path(f"{folder_name}/{file_name}")
    file = ctx.web.get_file_by_server_relative_url(file_path)
    ctx.load(file, ["Exists"])
    ctx.execute_query()

    if not file.exists:
        return {"success": False, "message": f"File '{file_name}' does not exist in '{folder_name}'"}

    file.delete_object()
    ctx.execute_query()
    return {"success": True, "message": f"File '{file_name}' deleted successfully"}


def download_document(
    folder_name: str,
    file_name: str,
    local_path: str,
) -> Dict[str, Any]:
    """Download a SharePoint file to *local_path* (with fallback to ./downloads)."""
    ctx = get_sp_context()
    logger.info("Downloading '%s/%s' → '%s'", folder_name, file_name, local_path)

    file = ctx.web.get_file_by_server_relative_url(_sp_path(f"{folder_name}/{file_name}"))
    ctx.load(file, ["Exists", "Length", "Name"])
    ctx.execute_query()

    if not file.exists:
        return {"success": False, "error": f"File '{file_name}' not found in '{folder_name}'"}

    buf = io.BytesIO()
    file.download(buf)
    ctx.execute_query()
    content_bytes = buf.getvalue()

    def _save(path: str) -> Dict[str, Any]:
        try:
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(path, "wb") as fh:
                fh.write(content_bytes)
            if os.path.exists(path) and os.path.getsize(path) == len(content_bytes):
                return {"success": True, "path": os.path.abspath(path), "size": len(content_bytes)}
            raise IOError("File verification failed after write")
        except Exception as exc:
            logger.error("Save failed for '%s': %s", path, exc)
            return {"success": False, "error": str(exc)}

    primary = _save(local_path)
    if primary["success"]:
        return {**primary, "method": "primary"}

    logger.warning("Primary save failed (%s), trying fallback", primary["error"])
    fallback_dir = "./downloads"
    os.makedirs(fallback_dir, exist_ok=True)
    fallback = _save(os.path.join(fallback_dir, file_name))
    if fallback["success"]:
        return {**fallback, "method": "fallback", "primary_error": primary["error"]}

    return {"success": False, "error": "Both primary and fallback saves failed", "primary_error": primary["error"], "fallback_error": fallback["error"]}
