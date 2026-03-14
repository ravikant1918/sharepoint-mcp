"""MCP tool registrations for document operations."""
from __future__ import annotations

import asyncio
import os
from typing import Any

from ..server import mcp
from ..services.document_service import (
    delete_document as _delete_document,
)
from ..services.document_service import (
    download_document as _download_document,
)
from ..services.document_service import (
    get_document_content as _get_document_content,
)
from ..services.document_service import (
    list_documents as _list_documents,
)
from ..services.document_service import (
    search_documents as _search_documents,
)
from ..services.document_service import (
    update_document as _update_document,
)
from ..services.document_service import (
    upload_document as _upload_document,
)
from ..services.document_service import (
    upload_from_path as _upload_from_path,
)
from ..config import get_settings


def _get_default_folder() -> str:
    """Get the default folder based on configuration.
    
    Returns:
        Default folder path respecting SHP_DOC_LIBRARY or using 'root' for Graph API.
    """
    settings = get_settings()
    
    # If user explicitly set a subfolder scope, use it
    if settings.shp_doc_library:
        return settings.shp_doc_library
    
    # For Graph API, use empty string (represents root of default drive)
    # The client will handle normalization if "Shared Documents" is passed
    if settings.shp_api_type in ["graph", "graphql"]:
        return ""  # Empty = root of document library in Graph API
    
    # For Office365 API, use the configured library name
    return settings.shp_library_name


@mcp.tool(
    name="List_SharePoint_Documents",
    description=(
        "List all documents (with metadata) inside a SharePoint folder. "
        "For Graph API, use empty string or 'root' for the document library root. "
        "For nested folders, use paths like 'Reports' or 'Reports/2024'."
    ),
)
async def list_documents_tool(folder_name: str = "") -> list[dict[str, Any]]:
    """Lists enterprise documents within a specified SharePoint path.

    Args:
        folder_name: The target relative SharePoint directory string.
                     Defaults to empty string (root of document library).

    Returns:
        A list of dictionaries containing file metadata and sizing.
    """
    # Use configured default if folder_name is empty
    if not folder_name:
        folder_name = _get_default_folder()
    
    return await asyncio.to_thread(_list_documents, folder_name)


@mcp.tool(
    name="Search_SharePoint",
    description=(
        "Search SharePoint for documents using Keyword Query Language (KQL). "
        "Useful for finding files when you don't know their exact folder path. "
        "Returns up to row_limit results with metadata."
    ),
)
async def search_documents_tool(query: str, row_limit: int = 20) -> list[dict[str, Any]]:
    """Searches SharePoint documents using Keyword Query Language (KQL).

    Args:
        query: The semantic search string.
        row_limit: Maximum number of results to retrieve.

    Returns:
        A list of matching document attributes.
    """
    return await asyncio.to_thread(_search_documents, query, row_limit)


@mcp.tool(
    name="Get_Document_Content",
    description=(
        "Retrieve and decode the content of a SharePoint document. "
        "Supports PDF, Word, Excel, and plain-text files. "
        "For files in the document library root, use empty string for folder_name."
    ),
)
async def get_document_content_tool(folder_name: str = "", file_name: str = "") -> dict[str, Any]:
    """Retrieves and parses the substantive content of a target SharePoint file.

    Args:
        folder_name: Directory containing target file. Use empty string for root.
        file_name: Exact file name including extension.

    Returns:
        Dictionary containing extracted text, page schemas, or binary payloads.
    """
    # Use default folder if not specified
    if not folder_name:
        folder_name = _get_default_folder()
    
    return await asyncio.to_thread(_get_document_content, folder_name, file_name)


@mcp.tool(
    name="Upload_Document",
    description=(
        "Upload a new document to a SharePoint folder. "
        "Pass content as a UTF-8 string or Base64-encoded bytes. "
        "Use empty string for folder_name to upload to document library root."
    ),
)
async def upload_document_tool(
    file_name: str,
    content: str,
    folder_name: str = "",
    is_base64: bool = False,
) -> dict[str, Any]:
    """Uploads document payload material to SharePoint.

    Args:
        file_name: Intended destination filename.
        content: Raw document string or base64 blob.
        folder_name: Target remote repository path. Use empty string for root.
        is_base64: Boolean indicating payload decoding.

    Returns:
        Dictionary containing the success status and remote file structure.
    """
    # Use default folder if not specified
    if not folder_name:
        folder_name = _get_default_folder()
    
    return await asyncio.to_thread(_upload_document, folder_name, file_name, content, is_base64)


@mcp.tool(
    name="Upload_Document_From_Path",
    description=(
        "Upload a local file directly to SharePoint without converting to Base64 first. "
        "Use empty string for folder_name to upload to document library root."
    ),
)
async def upload_from_path_tool(
    folder_name: str = "",
    file_path: str = "",
    new_file_name: str | None = None,
) -> dict[str, Any]:
    """Uploads an existing local system file into the target remote environment.

    Security Note: Protects against arbitrary system reads (LFI) using whitelist approach.
    
    Args:
        folder_name: Remote destination folder pattern. Use empty string for root.
        file_path: Absolute local path to source artifact.
        new_file_name: Optional string override for uploaded filename.
    
    Returns:
        Dictionary containing success flag and created node structure.
    
    Raises:
        ValueError: If file path points to an invalid or system-restricted location.
    """
    from pathlib import Path
    
    # Use default folder if not specified
    if not folder_name:
        folder_name = _get_default_folder()
    
    # Enhanced LFI Protection with whitelist approach and symlink resolution
    ALLOWED_DIRS = [
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Desktop"),
        "/tmp",
        os.getcwd(),  # Current working directory
    ]
    
    try:
        # Resolve to absolute path and check for symlink attacks (strict=True requires file exists)
        safe_target = Path(file_path).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"Invalid file path or file does not exist: {file_path}") from exc
    
    # Verify file is within allowed directories
    is_allowed = False
    for allowed_dir in ALLOWED_DIRS:
        try:
            resolved_allowed = Path(allowed_dir).resolve()
            if safe_target.is_relative_to(resolved_allowed):
                is_allowed = True
                break
        except (ValueError, OSError):
            continue
    
    if not is_allowed:
        raise ValueError(
            f"File path outside allowed directories. "
            f"Allowed: Downloads, Documents, Desktop, /tmp, current directory"
        )
    
    # Additional safety checks
    if not safe_target.is_file():
        raise ValueError("Path must be a regular file")
    
    if safe_target.stat().st_size > 100 * 1024 * 1024:  # 100MB limit
        raise ValueError("File exceeds maximum upload size (100MB)")
         
    return await asyncio.to_thread(_upload_from_path, folder_name, str(safe_target), new_file_name)


@mcp.tool(
    name="Update_Document",
    description=(
        "Overwrite the content of an existing SharePoint document. "
        "Use empty string for folder_name for files in document library root."
    ),
)
async def update_document_tool(
    folder_name: str = "",
    file_name: str = "",
    content: str = "",
    is_base64: bool = False,
) -> dict[str, Any]:
    """Mutates an existing document in place with overwrite semantics.
    
    Args:
        folder_name: Remote collection name where artifact exists. Use empty string for root.
        file_name: Target filename to override.
        content: The new text or base64 binary block.
        is_base64: Setting if binary format.

    Returns:
        Dictionary highlighting successful replacement or failure.
    """
    # Use default folder if not specified
    if not folder_name:
        folder_name = _get_default_folder()
    
    return await asyncio.to_thread(_update_document, folder_name, file_name, content, is_base64)


@mcp.tool(
    name="Delete_Document",
    description=(
        "Permanently delete a document from a SharePoint folder. "
        "Use empty string for folder_name for files in document library root."
    ),
)
async def delete_document_tool(folder_name: str = "", file_name: str = "") -> dict[str, Any]:
    """Unlinks and physically deletes a document node from SharePoint.

    Args:
        folder_name: Virtual directory structure of the target asset. Use empty string for root.
        file_name: Entity label to be removed.
        
    Returns:
        Dictionary signifying the boolean success pattern.
    """
    # Use default folder if not specified
    if not folder_name:
        folder_name = _get_default_folder()
    
    return await asyncio.to_thread(_delete_document, folder_name, file_name)


@mcp.tool(
    name="Download_Document",
    description=(
        "Download a SharePoint document to the local filesystem "
        "(with automatic fallback to ./downloads/). "
        "Use empty string for folder_name for files in document library root."
    ),
)
async def download_document_tool(
    folder_name: str = "", file_name: str = "", local_path: str = "",
) -> dict[str, Any]:
    """Hydrates a remote SharePoint asset to local active system storage.

    Args:
        folder_name: Source location inside SharePoint. Use empty string for root.
        file_name: Artifact identity text.
        local_path: Intended active destination system path.

    Returns:
        Dictionary including operation success states and verified file footprint.
    """
    # Use default folder if not specified
    if not folder_name:
        folder_name = _get_default_folder()
    
    return await asyncio.to_thread(_download_document, folder_name, file_name, local_path)
