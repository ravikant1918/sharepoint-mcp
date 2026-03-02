"""Unified document service supporting both Office365 and Graph APIs."""
from __future__ import annotations

import logging
from typing import Any

from ..core import get_sp_context

logger = logging.getLogger(__name__)


def list_documents(folder_name: str) -> list[dict[str, Any]]:
    """List all files in *folder_name*."""
    client = get_sp_context()
    
    if client.api_type in ("graph", "graphql"):
        from . import document_service_graph
        return document_service_graph.list_documents(folder_name)
    else:
        from . import document_service_office365
        return document_service_office365.list_documents(folder_name)


def search_documents(query_text: str, row_limit: int = 20) -> list[dict[str, Any]]:
    """Search SharePoint documents using query text."""
    client = get_sp_context()
    
    if client.api_type in ("graph", "graphql"):
        from . import document_service_graph
        return document_service_graph.search_documents(query_text, row_limit)
    else:
        from . import document_service_office365
        return document_service_office365.search_documents(query_text, row_limit)


def get_document_content(folder_name: str, file_name: str) -> dict[str, Any]:
    """Download and decode a file, returning its content."""
    client = get_sp_context()
    
    if client.api_type in ("graph", "graphql"):
        from . import document_service_graph
        return document_service_graph.get_document_content(folder_name, file_name)
    else:
        from . import document_service_office365
        return document_service_office365.get_document_content(folder_name, file_name)


def upload_document(
    folder_name: str,
    file_name: str,
    content: str,
    is_base64: bool = False,
) -> dict[str, Any]:
    """Upload *file_name* with *content* to *folder_name*."""
    client = get_sp_context()
    
    if client.api_type in ("graph", "graphql"):
        from . import document_service_graph
        return document_service_graph.upload_document(folder_name, file_name, content, is_base64)
    else:
        from . import document_service_office365
        return document_service_office365.upload_document(folder_name, file_name, content, is_base64)


def upload_from_path(
    folder_name: str,
    file_path: str,
    new_name: str | None = None,
) -> dict[str, Any]:
    """Upload a local file at *file_path* to *folder_name*."""
    client = get_sp_context()
    
    if client.api_type in ("graph", "graphql"):
        from . import document_service_graph
        return document_service_graph.upload_from_path(folder_name, file_path, new_name)
    else:
        from . import document_service_office365
        return document_service_office365.upload_from_path(folder_name, file_path, new_name)


def update_document(
    folder_name: str,
    file_name: str,
    content: str,
    is_base64: bool = False,
) -> dict[str, Any]:
    """Overwrite *file_name* in *folder_name* with new *content*."""
    client = get_sp_context()
    
    if client.api_type in ("graph", "graphql"):
        from . import document_service_graph
        return document_service_graph.update_document(folder_name, file_name, content, is_base64)
    else:
        from . import document_service_office365
        return document_service_office365.update_document(folder_name, file_name, content, is_base64)


def delete_document(folder_name: str, file_name: str) -> dict[str, Any]:
    """Delete *file_name* from *folder_name*."""
    client = get_sp_context()
    
    if client.api_type in ("graph", "graphql"):
        from . import document_service_graph
        return document_service_graph.delete_document(folder_name, file_name)
    else:
        from . import document_service_office365
        return document_service_office365.delete_document(folder_name, file_name)


def download_document(
    folder_name: str,
    file_name: str,
    local_path: str,
) -> dict[str, Any]:
    """Download a SharePoint file to *local_path* (fallback: system temp)."""
    client = get_sp_context()
    
    if client.api_type in ("graph", "graphql"):
        from . import document_service_graph
        return document_service_graph.download_document(folder_name, file_name, local_path)
    else:
        from . import document_service_office365
        return document_service_graph.download_document(folder_name, file_name, local_path)
