"""Custom exceptions for mcp-sharepoint."""


class SharePointError(Exception):
    """Base exception for all SharePoint MCP errors."""


class SharePointConfigError(SharePointError):
    """Raised when required configuration / environment variables are missing or invalid."""


class SharePointConnectionError(SharePointError):
    """Raised when the SharePoint client context cannot be established."""


class SharePointOperationError(SharePointError):
    """Raised when a SharePoint API call fails."""

    def __init__(self, operation: str, detail: str) -> None:
        self.operation = operation
        self.detail = detail
        super().__init__(f"Operation '{operation}' failed: {detail}")
