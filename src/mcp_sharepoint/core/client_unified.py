"""SharePoint client factory supporting both Office365 and Graph APIs.

Provides a unified interface for SharePoint operations using either:
- Office365 REST API (legacy/traditional)
- Microsoft Graph API (modern/GraphQL-based)
"""
from __future__ import annotations

import logging
import threading
import time
from functools import lru_cache
from typing import Any, Protocol
from urllib.parse import urlparse

import msal
import requests
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config import get_settings
from ..exceptions import SharePointConnectionError

logger = logging.getLogger(__name__)


class TokenCache:
    """Thread-safe token cache with expiry tracking.
    
    This class manages access tokens with automatic expiry detection,
    ensuring tokens are refreshed before they expire to prevent API failures.
    """
    
    def __init__(self):
        """Initialize empty token cache with thread lock."""
        self.token: str | None = None
        self.expires_at: float = 0
        self._lock = threading.Lock()
    
    def set_token(self, token: str, expires_in: int):
        """Set token with expiry time.
        
        Args:
            token: Access token string
            expires_in: Token validity duration in seconds
        """
        with self._lock:
            self.token = token
            self.expires_at = time.time() + expires_in
            logger.info(
                f"Token cached. Expires in {expires_in}s (at {time.ctime(self.expires_at)})"
            )
    
    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Check if token is expired or will expire soon.
        
        Args:
            buffer_seconds: Refresh buffer time before actual expiry (default: 5 minutes)
            
        Returns:
            True if token is expired or missing, False otherwise
        """
        with self._lock:
            if not self.token:
                return True
            # Refresh 5 minutes (300s) before actual expiry to prevent edge cases
            return time.time() >= (self.expires_at - buffer_seconds)
    
    def get_token(self) -> str | None:
        """Get current token if valid.
        
        Returns:
            Valid token string or None if expired/missing
        """
        with self._lock:
            return self.token if not self.is_expired() else None


# Global token cache for Graph API (one per application instance)
_graph_token_cache = TokenCache()


class SharePointClient(Protocol):
    """Protocol defining the interface for SharePoint clients."""
    
    api_type: str
    
    def __repr__(self) -> str:
        """String representation of the client."""
        ...


class Office365Client:
    """Wrapper for Office365 REST API ClientContext."""
    
    def __init__(self, ctx: ClientContext):
        """Initialize with Office365 ClientContext.
        
        Args:
            ctx: Authenticated ClientContext instance
        """
        self.ctx = ctx
        self.api_type = "office365"
    
    def __repr__(self) -> str:
        return f"Office365Client(site={self.ctx.base_url})"


class GraphClient:
    """Microsoft Graph API client for SharePoint operations with connection pooling."""

    def __init__(self, access_token: str, site_url: str):
        """Initialize Graph client with access token and site URL.
        
        Args:
            access_token: Microsoft Graph API access token
            site_url: SharePoint site URL
        """
        self.access_token = access_token
        self.site_url = site_url
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.api_type = "graph"
        
        # Extract site components from URL
        parsed = urlparse(site_url)
        self.hostname = parsed.netloc
        # Extract site path (e.g., /sites/sitename)
        self.site_path = parsed.path.rstrip('/')
        
        # Create session with connection pooling and retry strategy
        self.session = requests.Session()
        
        # Configure retry strategy for transient errors
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "PATCH"]
        )
        
        # Add adapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20,
            pool_block=False
        )
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        
        # Also keep headers dict for backwards compatibility
        self.headers = self.session.headers.copy()
        
        # Configurable timeouts (connect, read)
        self.timeout = (5, 30)
        
        # Cache site ID and drive ID
        self._site_id_cache: str | None = None
        self._drive_id_cache: str | None = None
        
        # Initialize site and drive information
        self._initialize_site_info()
    
    def _initialize_site_info(self):
        """Initialize site and drive information on client creation.
        
        This proactively fetches site ID and default drive ID to:
        1. Validate credentials and access
        2. Enable more reliable API calls using drive IDs
        3. Detect configuration issues early
        """
        try:
            # Get site ID
            site_resource = f"{self.hostname}:{self.site_path}"
            site_url = f"{self.base_url}/sites/{site_resource}"
            
            response = self.session.get(site_url, timeout=self.timeout)
            response.raise_for_status()
            site_data = response.json()
            self._site_id_cache = site_data.get("id")
            
            if self._site_id_cache:
                # Get default drive (document library)
                drive_url = f"{self.base_url}/sites/{self._site_id_cache}/drive"
                response = self.session.get(drive_url, timeout=self.timeout)
                response.raise_for_status()
                drive_data = response.json()
                self._drive_id_cache = drive_data.get("id")
                
                site_snip = (self._site_id_cache or "")[:20]
                drive_snip = (self._drive_id_cache or "")[:20]
                logger.info(
                    "Initialized Graph client - site_id=%s..., drive_id=%s...",
                    site_snip,
                    drive_snip,
                )
        except Exception as exc:
            logger.warning(f"Could not initialize site/drive info: {exc}")
            logger.warning("Client will use fallback path-based URLs")
        
    def _get_site_id(self) -> str:
        """Get the SharePoint site ID from the site URL (cached)."""
        if self._site_id_cache:
            return self._site_id_cache
            
        # Format: /sites/{hostname}:{site_path}
        site_resource = f"{self.hostname}:{self.site_path}"
        url = f"{self.base_url}/sites/{site_resource}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            self._site_id_cache = response.json().get("id", "")
            return self._site_id_cache
        except Exception as exc:
            logger.error(f"Failed to get site ID: {exc}")
            # Fallback: try root site
            try:
                url = f"{self.base_url}/sites/{self.hostname}:{self.site_path}"
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                self._site_id_cache = response.json().get("id", "")
                return self._site_id_cache
            except Exception as e:
                logger.error(f"Fallback site ID lookup failed: {e}")
                raise SharePointConnectionError(f"Cannot determine site ID: {exc}") from exc
    
    def normalize_path(self, path: str) -> str:
        """Normalize folder path for Microsoft Graph API.
        
        Maps SharePoint library names to Graph API paths, as Graph API's
        default drive root already represents the "Shared Documents" library.
        
        Args:
            path: Input path (e.g., "Shared Documents", "Shared Documents/Reports")
            
        Returns:
            Normalized path for Graph API (e.g., "", "Reports")
        """
        if not path:
            return ""
        
        # Remove leading/trailing slashes and spaces
        path = path.strip().strip("/")
        
        # Map common SharePoint library names to Graph API paths
        # "Shared Documents" is the default library, which is the drive root in Graph API
        library_mappings = {
            "shared documents": "",  # Root of default document library
            "documents": "",
            "sitepages": "SitePages",
            "site pages": "SitePages",
            "style library": "Style Library",
        }
        
        # Check if path starts with a known library name
        path_lower = path.lower()
        for library_name, graph_path in library_mappings.items():
            if path_lower == library_name:
                # Exact match - return mapped path
                logger.debug(f"Path mapping: '{path}' → '{graph_path or 'root'}'")
                return graph_path
            elif path_lower.startswith(library_name + "/"):
                # Path within library - strip library name and keep rest
                remaining_path = path[len(library_name)+1:]
                result = f"{graph_path}/{remaining_path}" if graph_path else remaining_path
                logger.debug(f"Path mapping: '{path}' → '{result}'")
                return result
        
        # Not a known library - return as-is
        return path
    
    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a GET request to Graph API with automatic retry for common path issues.
        
        Args:
            endpoint: API endpoint (relative to base_url)
            params: Optional query parameters
            
        Returns:
            Response JSON data
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as exc:
            # Handle 404 errors that might be due to "Shared Documents" path issues
            if exc.response is not None and exc.response.status_code == 404:
                logger.warning(f"GET {url} returned 404")
                
                # Check if this is a "Shared Documents" path issue
                if "Shared%20Documents" in url or "Shared Documents" in endpoint:
                    logger.info("Detected 'Shared Documents' path; retrying")

                    # Try to fix the path by removing "Shared Documents"
                    fixed_endpoint = endpoint.replace("/Shared Documents", "")
                    fixed_endpoint = fixed_endpoint.replace("/Shared%20Documents", "")
                    fixed_endpoint = fixed_endpoint.replace("Shared Documents/", "")
                    fixed_endpoint = fixed_endpoint.replace("Shared%20Documents/", "")

                    if fixed_endpoint != endpoint:
                        logger.info("Retrying with fixed endpoint: %s", fixed_endpoint)
                        fixed_url = f"{self.base_url}/{fixed_endpoint.lstrip('/')}"
                        try:
                            response = self.session.get(
                                fixed_url,
                                params=params,
                                timeout=self.timeout,
                            )
                            response.raise_for_status()
                            logger.info("Retry successful with normalized path")
                            return response.json()
                        except Exception as retry_exc:
                            logger.error("Retry also failed: %s", retry_exc)
                
                # Log response details for debugging
                logger.error(f"Response: {exc.response.text}")
            
            raise SharePointConnectionError(f"Graph API GET failed: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            logger.error(f"GET {url} failed: {exc}")
            if hasattr(exc, 'response') and exc.response is not None:
                logger.error(f"Response: {exc.response.text}")
            raise SharePointConnectionError(f"Graph API GET failed: {exc}") from exc
    
    def post(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a POST request to Graph API.
        
        Args:
            endpoint: API endpoint (relative to base_url)
            data: Request body data
            
        Returns:
            Response JSON data
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            logger.error(f"POST {url} failed: {exc}")
            if hasattr(exc, 'response') and exc.response is not None:
                logger.error(f"Response: {exc.response.text}")
            raise SharePointConnectionError(f"Graph API POST failed: {exc}") from exc
    
    def put(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a PUT request to Graph API.
        
        Args:
            endpoint: API endpoint (relative to base_url)
            data: Request body data
            
        Returns:
            Response JSON data
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.put(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as exc:
            logger.error(f"PUT {url} failed: {exc}")
            if hasattr(exc, 'response') and exc.response is not None:
                logger.error(f"Response: {exc.response.text}")
            raise SharePointConnectionError(f"Graph API PUT failed: {exc}") from exc
    
    def delete(self, endpoint: str) -> bool:
        """Make a DELETE request to Graph API.
        
        Args:
            endpoint: API endpoint (relative to base_url)
            
        Returns:
            True if successful
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.delete(url, timeout=self.timeout)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as exc:
            logger.error(f"DELETE {url} failed: {exc}")
            if hasattr(exc, 'response') and exc.response is not None:
                logger.error(f"Response: {exc.response.text}")
            raise SharePointConnectionError(f"Graph API DELETE failed: {exc}") from exc
    
    def download(self, endpoint: str) -> bytes:
        """Download binary content from Graph API.
        
        Args:
            endpoint: API endpoint (relative to base_url)
            
        Returns:
            Binary content
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            # Use longer timeout for downloads
            response = self.session.get(url, timeout=(5, 60))
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as exc:
            logger.error(f"Download from {url} failed: {exc}")
            raise SharePointConnectionError(f"Graph API download failed: {exc}") from exc
    
    def upload(self, endpoint: str, content: bytes) -> dict[str, Any]:
        """Upload binary content to Graph API.
        
        Args:
            endpoint: API endpoint (relative to base_url)
            content: Binary content to upload
            
        Returns:
            Response JSON data
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        # Create separate headers for upload (different content-type)
        upload_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/octet-stream",
        }
        try:
            # Use longer timeout for uploads
            response = self.session.put(url, headers=upload_headers, data=content, timeout=(5, 60))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            logger.error(f"Upload to {url} failed: {exc}")
            if hasattr(exc, 'response') and exc.response is not None:
                logger.error(f"Response: {exc.response.text}")
            raise SharePointConnectionError(f"Graph API upload failed: {exc}") from exc
    
    def __repr__(self) -> str:
        return f"GraphClient(site={self.site_url})"


def get_sp_context() -> Office365Client | GraphClient:
    """Return an authenticated SharePoint client with automatic token refresh.

    The client type is determined by the SHP_API_TYPE environment variable:
    - "office365" (default): Uses Office365 REST API
    - "graph": Uses Microsoft Graph API with automatic token refresh

    For Graph API clients, tokens are automatically refreshed when they expire
    or are close to expiring (5 min buffer), ensuring uninterrupted API access.

    Raises:
        SharePointConnectionError: if the client cannot be established.
    """
    settings = get_settings()
    
    if settings.shp_api_type == "graph":
        logger.debug("Using Microsoft Graph API client")
        return _create_graph_client(settings)
    else:
        logger.debug("Using Office365 REST API client")
        return _create_office365_client(settings)


@lru_cache(maxsize=1)
def _get_msal_app(tenant_id: str, client_id: str, client_secret: str):
    """Create and cache MSAL application instance.
    
    Args:
        tenant_id: Azure AD tenant ID
        client_id: Application (client) ID
        client_secret: Application secret
        
    Returns:
        Configured ConfidentialClientApplication instance
    """
    return msal.ConfidentialClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        client_credential=client_secret,
    )


def _acquire_graph_token(settings) -> str:
    """Acquire a new Graph API token with retry logic.
    
    Args:
        settings: Application settings containing credentials
        
    Returns:
        Valid access token
        
    Raises:
        SharePointConnectionError: If token acquisition fails after retries
    """
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            app = _get_msal_app(
                settings.shp_tenant_id,
                settings.shp_id_app,
                settings.shp_id_app_secret
            )
            scopes = ["https://graph.microsoft.com/.default"]
            
            logger.info(
                f"Acquiring Graph API token (attempt {attempt + 1}/{max_retries})..."
            )
            result = app.acquire_token_for_client(scopes=scopes)
            
            if "access_token" not in result:
                error = result.get("error_description", result.get("error", "Unknown error"))
                logger.error(f"Token acquisition failed: {error}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise SharePointConnectionError(
                        f"Failed to acquire token after {max_retries} attempts: {error}"
                    )
            
            # Successfully acquired token
            expires_in = result.get("expires_in", 3600)  # Default 1 hour
            _graph_token_cache.set_token(result["access_token"], expires_in)
            
            logger.info(f"✓ Token acquired successfully. Valid for {expires_in}s")
            return result["access_token"]
            
        except SharePointConnectionError:
            raise
        except Exception as e:
            logger.exception(f"Exception during token acquisition: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                raise SharePointConnectionError(
                    f"Failed to acquire token: {e}"
                ) from e
    
    # Should never reach here, but just in case
    raise SharePointConnectionError("Token acquisition failed unexpectedly")


def _create_office365_client(settings) -> Office365Client:
    """Create an Office365 REST API client.
    
    Office365 REST API handles token management internally.
    """
    try:
        credentials = ClientCredential(settings.shp_id_app, settings.shp_id_app_secret)
        ctx = ClientContext(settings.shp_site_url).with_credentials(credentials)
        logger.info("Office365 client context initialized for %s", settings.shp_site_url)
        return Office365Client(ctx)
    except Exception as exc:
        msg = f"Failed to create Office365 client: {exc}"
        logger.error(msg)
        raise SharePointConnectionError(msg) from exc


def _create_graph_client(settings) -> GraphClient:
    """Create a Microsoft Graph API client with automatic token refresh.
    
    This function checks if a valid cached token exists. If the token is expired
    or will expire soon (within 5 minutes), it acquires a fresh token automatically.
    
    Args:
        settings: Application settings containing credentials and site URL
        
    Returns:
        GraphClient instance with valid access token
        
    Raises:
        SharePointConnectionError: If client creation or token acquisition fails
    """
    try:
        # Try to get cached token first
        token = _graph_token_cache.get_token()
        
        # If token is expired or missing, acquire new one
        if not token:
            logger.debug("Token expired or missing, acquiring new token...")
            token = _acquire_graph_token(settings)
        else:
            logger.debug("Using cached token")
        
        # Create client with valid token
        client = GraphClient(token, settings.shp_site_url)
        logger.info("Microsoft Graph API client initialized for %s", settings.shp_site_url)
        return client
        
    except SharePointConnectionError:
        raise
    except Exception as exc:
        msg = f"Failed to create Graph API client: {exc}"
        logger.error(msg)
        raise SharePointConnectionError(msg) from exc
