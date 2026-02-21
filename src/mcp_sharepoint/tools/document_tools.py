"""MCP tool registrations for document operations."""
from __future__ import annotations

import asyncio

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
async def list_documents_tool(folder_name: str):
    return await asyncio.to_thread(_list_documents, folder_name)


@mcp.tool(
    name="Get_Document_Content",
    description=(
        "Retrieve and decode the content of a SharePoint document. "
        "Supports PDF, Word, Excel, and plain-text files."
    ),
)
async def get_document_content_tool(folder_name: str, file_name: str):
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
):
    return await asyncio.to_thread(_upload_document, folder_name, file_name, content, is_base64)


@mcp.tool(
    name="Upload_Document_From_Path",
    description="Upload a local file directly to SharePoint without converting to Base64 first.",
)
async def upload_from_path_tool(
    folder_name: str,
    file_path: str,
    new_file_name: str | None = None,
):
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
):
    return await asyncio.to_thread(_update_document, folder_name, file_name, content, is_base64)


@mcp.tool(
    name="Delete_Document",
    description="Permanently delete a document from a SharePoint folder.",
)
async def delete_document_tool(folder_name: str, file_name: str):
    return await asyncio.to_thread(_delete_document, folder_name, file_name)


@mcp.tool(
    name="Download_Document",
    description=(
        "Download a SharePoint document to the local filesystem "
        "(with automatic fallback to ./downloads/)."
    ),
)
async def download_document_tool(folder_name: str, file_name: str, local_path: str):
    return await asyncio.to_thread(_download_document, folder_name, file_name, local_path)
