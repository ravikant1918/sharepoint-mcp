"""SharePoint Graph API client.

Provides a cached Graph API client with MSAL authentication.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any
from urllib.parse import quote, urlparse

import msal
import requests

from ..config import get_settings
from ..exceptions import SharePointConnectionError

logger = logging.getLogger(__name__)


class GraphClient:
    """Microsoft Graph API client for SharePoint operations."""

    def __init__(self, access_token: str, site_url: str):
        """Initialize Graph client with access token and site URL.
        
        Args:
            access_token: Microsoft Graph API access token
            site_url: SharePoint site URL
        """
        self.access_token = access_token
        self.site_url = site_url
        self.base_url = "https://graph.microsoft.com/v1.0"
        
        # Extract site components from URL
        parsed = urlparse(site_url)
        self.hostname = parsed.netloc
        # Extract site path (e.g., /sites/sitename)
        self.site_path = parsed.path.rstrip('/')
        
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
    def _get_site_id(self) -> str:
        """Get the SharePoint site ID from the site URL."""
        # Format: /sites/{hostname}:{site_path}
        site_resource = f"{self.hostname}:{self.site_path}"
        url = f"{self.base_url}/sites/{site_resource}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json().get("id", "")
        except Exception as exc:
            logger.error(f"Failed to get site ID: {exc}")
            # Fallback: try root site
            try:
                url = f"{self.base_url}/sites/{self.hostname}:{self.site_path}"
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                return response.json().get("id", "")
            except Exception as e:
                logger.error(f"Fallback site ID lookup failed: {e}")
                raise SharePointConnectionError(f"Cannot determine site ID: {exc}") from exc
    
    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a GET request to Graph API.
        
        Args:
            endpoint: API endpoint (relative to base_url)
            params: Optional query parameters
            
        Returns:
            Response JSON data
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
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
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
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
            response = requests.put(url, headers=self.headers, json=data, timeout=30)
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
            response = requests.delete(url, headers=self.headers, timeout=30)
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
            response = requests.get(url, headers=self.headers, timeout=60)
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
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/octet-stream",
        }
        try:
            response = requests.put(url, headers=headers, data=content, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            logger.error(f"Upload to {url} failed: {exc}")
            if hasattr(exc, 'response') and exc.response is not None:
                logger.error(f"Response: {exc.response.text}")
            raise SharePointConnectionError(f"Graph API upload failed: {exc}") from exc


@lru_cache(maxsize=1)
def get_sp_context() -> GraphClient:
    """Return a cached, authenticated Microsoft Graph API client.

    Raises:
        SharePointConnectionError: if the client cannot be established.
    """
    settings = get_settings()
    try:
        # Create MSAL confidential client application
        app = msal.ConfidentialClientApplication(
            settings.shp_id_app,
            authority=f"https://login.microsoftonline.com/{settings.shp_tenant_id}",
            client_credential=settings.shp_id_app_secret,
        )
        
        # Acquire token for Microsoft Graph
        scopes = ["https://graph.microsoft.com/.default"]
        result = app.acquire_token_for_client(scopes=scopes)
        
        if "access_token" not in result:
            error_desc = result.get("error_description", "Unknown error")
            raise SharePointConnectionError(f"Failed to acquire access token: {error_desc}")
        
        access_token = result["access_token"]
        client = GraphClient(access_token, settings.shp_site_url)
        
        logger.info("Microsoft Graph API client initialized for %s", settings.shp_site_url)
        return client
        
    except Exception as exc:
        msg = f"Failed to create Graph API client: {exc}"
        logger.error(msg)
        raise SharePointConnectionError(msg) from exc
