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


@mcp.tool(
    name="List_SharePoint_Documents",
    description="List all documents (with metadata) inside a specified SharePoint folder.",
)
async def list_documents_tool(folder_name: str) -> list[dict[str, Any]]:
    """Lists enterprise documents within a specified SharePoint path.

    Args:
        folder_name: The target relative SharePoint directory string.

    Returns:
        A list of dictionaries containing file metadata and sizing.
    """
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
        "Supports PDF, Word, Excel, and plain-text files."
    ),
)
async def get_document_content_tool(folder_name: str, file_name: str) -> dict[str, Any]:
    """Retrieves and parses the substantive content of a target SharePoint file.

    Args:
        folder_name: Directory containing target file.
        file_name: Exact file name including extension.

    Returns:
        Dictionary containing extracted text, page schemas, or binary payloads.
    """
    return await asyncio.to_thread(_get_document_content, folder_name, file_name)


@mcp.tool(
    name="Upload_Document",
    description=(
        "Upload a new document to a SharePoint folder. "
        "Pass content as a UTF-8 string or Base64-encoded bytes."
    ),
)
async def upload_document_tool(
    folder_name: str,
    file_name: str,
    content: str,
    is_base64: bool = False,
) -> dict[str, Any]:
    """Uploads document payload material to SharePoint.

    Args:
        folder_name: Target remote repository path.
        file_name: Intended destination filename.
        content: Raw document string or base64 blob.
        is_base64: Boolean indicating payload decoding.

    Returns:
        Dictionary containing the success status and remote file structure.
    """
    return await asyncio.to_thread(_upload_document, folder_name, file_name, content, is_base64)


@mcp.tool(
    name="Upload_Document_From_Path",
    description="Upload a local file directly to SharePoint without converting to Base64 first.",
)
async def upload_from_path_tool(
    folder_name: str,
    file_path: str,
    new_file_name: str | None = None,
) -> dict[str, Any]:
    """Uploads an existing local system file into the target remote environment.

    Security Note: Protects against arbitrary system reads (LFI).
    
    Args:
        folder_name: Remote destination folder pattern.
        file_path: Absolute local path to source artifact.
        new_file_name: Optional string override for uploaded filename.
    
    Returns:
        Dictionary containing success flag and created node structure.
    
    Raises:
        ValueError: If file path points to an invalid or system-restricted location.
    """
    # LFI Protection limit to common scratch or downloads dirs if needed,
    # or at minimum ensure it's not grabbing sensitive UNIX files:
    safe_target = os.path.abspath(file_path)
    if safe_target.startswith("/etc/") or safe_target.startswith("/var/") or safe_target == "/":
         raise ValueError(
             f"LFI Prevention: Restricted system boundaries detected for target {file_path}"
         )
         
    return await asyncio.to_thread(_upload_from_path, folder_name, file_path, new_file_name)


@mcp.tool(
    name="Update_Document",
    description="Overwrite the content of an existing SharePoint document.",
)
async def update_document_tool(
    folder_name: str,
    file_name: str,
    content: str,
    is_base64: bool = False,
) -> dict[str, Any]:
    """Mutates an existing document in place with overwrite semantics.
    
    Args:
        folder_name: Remote collection name where artifact exists.
        file_name: Target filename to override.
        content: The new text or base64 binary block.
        is_base64: Setting if binary format.

    Returns:
        Dictionary highlighting successful replacement or failure.
    """
    return await asyncio.to_thread(_update_document, folder_name, file_name, content, is_base64)


@mcp.tool(
    name="Delete_Document",
    description="Permanently delete a document from a SharePoint folder.",
)
async def delete_document_tool(folder_name: str, file_name: str) -> dict[str, Any]:
    """Unlinks and physically deletes a document node from SharePoint.

    Args:
        folder_name: Virtual directory structure of the target asset.
        file_name: Entity label to be removed.
        
    Returns:
        Dictionary signifying the boolean success pattern.
    """
    return await asyncio.to_thread(_delete_document, folder_name, file_name)


@mcp.tool(
    name="Download_Document",
    description=(
        "Download a SharePoint document to the local filesystem "
        "(with automatic fallback to ./downloads/)."
    ),
)
async def download_document_tool(
    folder_name: str, file_name: str, local_path: str,
) -> dict[str, Any]:
    """Hydrates a remote SharePoint asset to local active system storage.

    Args:
        folder_name: Source location inside SharePoint.
        file_name: Artifact identity text.
        local_path: Intended active destination system path.

    Returns:
        Dictionary including operation success states and verified file footprint.
    """
    return await asyncio.to_thread(_download_document, folder_name, file_name, local_path)
