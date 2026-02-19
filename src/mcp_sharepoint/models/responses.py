"""Pydantic response models for all MCP tool return values.

Using typed models instead of raw dicts gives:
- Auto-validation of return shapes
- IDE auto-complete in consumers
- Clean JSON serialisation via .model_dump()
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared primitives
# ---------------------------------------------------------------------------

class FolderEntry(BaseModel):
    name: str
    url: Optional[str] = None
    created: Optional[str] = None
    modified: Optional[str] = None


class FileEntry(BaseModel):
    name: str
    url: Optional[str] = None
    size: Optional[int] = None
    created: Optional[str] = None
    modified: Optional[str] = None


class TreeNode(BaseModel):
    name: str
    path: Optional[str] = None
    type: str  # "folder" | "file"
    created: Optional[str] = None
    modified: Optional[str] = None
    size: Optional[int] = None
    children: List["TreeNode"] = Field(default_factory=list)
    error: Optional[str] = None


TreeNode.model_rebuild()  # required for self-referential model


# ---------------------------------------------------------------------------
# Operation responses
# ---------------------------------------------------------------------------

class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    file: Optional[Dict[str, str]] = None
    folder: Optional[Dict[str, str]] = None
    method: Optional[str] = None
    path: Optional[str] = None
    size: Optional[int] = None
    primary_error: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    detail: Optional[str] = None


# ---------------------------------------------------------------------------
# Content responses
# ---------------------------------------------------------------------------

class DocumentContent(BaseModel):
    name: str
    content_type: str                    # "text" | "binary"
    content: Optional[str] = None        # for text files
    content_base64: Optional[str] = None # for binary files
    original_type: Optional[str] = None  # "pdf" | "excel" | "word"
    size: int
    page_count: Optional[int] = None
    sheet_count: Optional[int] = None
    paragraph_count: Optional[int] = None


class MetadataResponse(BaseModel):
    success: bool = True
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    file: Optional[Dict[str, str]] = None
