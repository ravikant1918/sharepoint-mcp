"""SharePoint GraphQL client using Microsoft Graph GraphQL API.

Provides a true GraphQL client for SharePoint operations.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any
from urllib.parse import urlparse

import msal
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.requests import RequestsHTTPTransport

from ..config import get_settings
from ..exceptions import SharePointConnectionError

logger = logging.getLogger(__name__)


class GraphQLClient:
    """Microsoft Graph GraphQL API client for SharePoint operations."""

    def __init__(self, access_token: str, site_url: str):
        """Initialize GraphQL client with access token and site URL.
        
        Args:
            access_token: Microsoft Graph API access token
            site_url: SharePoint site URL
        """
        self.access_token = access_token
        self.site_url = site_url
        self.api_type = "graphql"
        
        # Microsoft Graph GraphQL endpoint (beta)
        # Note: GraphQL support is in beta, we'll use REST-style queries
        self.graphql_endpoint = "https://graph.microsoft.com/v1.0"
        
        # Extract site components
        parsed = urlparse(site_url)
        self.hostname = parsed.netloc
        self.site_path = parsed.path.rstrip('/')
        
        # Setup GraphQL transport
        self.transport = RequestsHTTPTransport(
            url=f"{self.graphql_endpoint}/$batch",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            verify=True,
            retries=3,
        )
        
        # Cache site ID and drive ID
        self._site_id_cache: str | None = None
        self._drive_id_cache: str | None = None
        
        # Initialize site and drive information
        self._initialize_site_info()
    
    def _initialize_site_info(self):
        """Initialize site and drive information on client creation.
        
        This proactively fetches site ID and default drive ID to:
        1. Validate credentials and access early
        2. Enable more reliable API calls using drive IDs
        3. Detect configuration issues immediately
        """
        import requests
        
        try:
            # Step 1: Get site ID
            site_resource = f"{self.hostname}:{self.site_path}"
            site_url = f"{self.graphql_endpoint}/sites/{site_resource}"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json",
            }
            
            logger.info(f"Fetching site info for {site_resource}")
            response = requests.get(site_url, headers=headers, timeout=30)
            response.raise_for_status()
            site_data = response.json()
            self._site_id_cache = site_data.get("id")
            
            if not self._site_id_cache:
                raise ValueError("Site ID not found in response")
            
            logger.info(f"✓ Site ID retrieved: {self._site_id_cache}")
            
            # Step 2: Get default drive ID
            logger.info(f"Fetching default drive for site {self._site_id_cache[:20]}...")
            drive_url = f"{self.graphql_endpoint}/sites/{self._site_id_cache}/drive"
            
            response = requests.get(drive_url, headers=headers, timeout=30)
            logger.debug(f"Drive API response status: {response.status_code}")
            
            if response.status_code == 404:
                logger.warning(f"⚠️ No default drive found (404). Attempting to list all drives...")
                
                # Try to get list of all drives
                drives_url = f"{self.graphql_endpoint}/sites/{self._site_id_cache}/drives"
                drives_response = requests.get(drives_url, headers=headers, timeout=30)
                drives_response.raise_for_status()
                drives_data = drives_response.json()
                
                drives = drives_data.get("value", [])
                logger.info(f"Found {len(drives)} drive(s) on this site:")
                for drive in drives:
                    logger.info(f"  - {drive.get('name')} (Type: {drive.get('driveType')}, ID: {drive.get('id')[:20]}...)")
                
                if drives:
                    # Use first available drive
                    self._drive_id_cache = drives[0].get("id")
                    logger.info(f"✓ Using drive: {drives[0].get('name')} (ID: {self._drive_id_cache[:20]}...)")
                else:
                    raise ValueError("No drives found on this SharePoint site")
            else:
                response.raise_for_status()
                drive_data = response.json()
                self._drive_id_cache = drive_data.get("id")
                drive_name = drive_data.get("name", "Unknown")
                logger.info(f"✓ Default drive retrieved: {drive_name} (ID: {self._drive_id_cache[:20]}...)")
            
            if not self._drive_id_cache:
                raise ValueError("Drive ID not found")
            
            logger.info(f"🎉 GraphQL client initialized successfully")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ HTTP error during site initialization: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise SharePointConnectionError(
                f"Failed to initialize SharePoint connection: {e}. "
                f"Please check credentials and site URL."
            ) from e
        except Exception as e:
            logger.error(f"❌ Unexpected error during site initialization: {e}")
            raise SharePointConnectionError(
                f"Failed to initialize SharePoint connection: {e}"
            ) from e
    
    def normalize_path(self, path: str) -> str:
        """Normalize folder path for Microsoft Graph API.
        
        Maps SharePoint library names to Graph API paths.
        
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
        library_mappings = {
            "shared documents": "",
            "documents": "",
            "sitepages": "SitePages",
            "site pages": "SitePages",
            "style library": "Style Library",
        }
        
        # Check if path starts with a known library name
        path_lower = path.lower()
        for library_name, graph_path in library_mappings.items():
            if path_lower == library_name:
                logger.debug(f"Path mapping: '{path}' → '{graph_path or 'root'}'")
                return graph_path
            elif path_lower.startswith(library_name + "/"):
                remaining_path = path[len(library_name)+1:]
                result = f"{graph_path}/{remaining_path}" if graph_path else remaining_path
                logger.debug(f"Path mapping: '{path}' → '{result}'")
                return result
        
        return path
        
    def _get_site_id(self) -> str:
        """Get the SharePoint site ID."""
        if self._site_id_cache:
            return self._site_id_cache
        
        import requests
        
        # Use REST endpoint to get site ID (required for subsequent GraphQL queries)
        site_resource = f"{self.hostname}:{self.site_path}"
        url = f"{self.graphql_endpoint}/sites/{site_resource}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            self._site_id_cache = response.json().get("id", "")
            logger.info(f"Retrieved site ID: {self._site_id_cache}")
            return self._site_id_cache
        except Exception as exc:
            logger.error(f"Failed to get site ID: {exc}")
            raise SharePointConnectionError(f"Cannot determine site ID: {exc}") from exc
    
    def execute_query(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a GraphQL query using batch requests.
        
        Args:
            query: GraphQL query string or REST endpoint path
            variables: Query variables
            
        Returns:
            Query result
        """
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        # If it's a REST-style path, execute directly
        if query.startswith("/"):
            url = f"{self.graphql_endpoint}{query}"
            try:
                response = requests.get(url, headers=headers, params=variables, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as exc:
                logger.error(f"Query failed: {exc}")
                if hasattr(exc, 'response') and exc.response is not None:
                    logger.error(f"Response: {exc.response.text}")
                raise SharePointConnectionError(f"GraphQL query failed: {exc}") from exc
        
        # For actual GraphQL queries (when Microsoft fully supports it)
        # This is a placeholder for future GraphQL support
        raise NotImplementedError("Pure GraphQL queries not yet supported by Microsoft Graph")
    
    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a GET request with automatic retry for common path issues.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            Response data
        """
        import requests
        
        url = f"{self.graphql_endpoint}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as exc:
            # Handle 404 errors that might be due to "Shared Documents" path issues
            if exc.response is not None and exc.response.status_code == 404:
                logger.warning(f"GET {url} returned 404")
                
                # Check if this is a "Shared Documents" path issue
                if "Shared%20Documents" in url or "Shared Documents" in endpoint:
                    logger.info("Detected 'Shared Documents' in path, attempting retry with normalized path")
                    
                    # Try to fix the path by removing "Shared Documents"
                    fixed_endpoint = endpoint.replace("/Shared Documents", "").replace("/Shared%20Documents", "")
                    fixed_endpoint = fixed_endpoint.replace("Shared Documents/", "").replace("Shared%20Documents/", "")
                    
                    if fixed_endpoint != endpoint:
                        logger.info(f"Retrying with fixed endpoint: {fixed_endpoint}")
                        fixed_url = f"{self.graphql_endpoint}/{fixed_endpoint.lstrip('/')}"
                        try:
                            response = requests.get(fixed_url, headers=headers, params=params, timeout=30)
                            response.raise_for_status()
                            logger.info("✓ Retry successful with normalized path")
                            return response.json()
                        except Exception as retry_exc:
                            logger.error(f"Retry also failed: {retry_exc}")
                
                # Log response details for debugging
                logger.error(f"Response: {exc.response.text}")
            
            raise SharePointConnectionError(f"API request failed: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            logger.error(f"GET {url} failed: {exc}")
            if hasattr(exc, 'response') and exc.response is not None:
                logger.error(f"Response: {exc.response.text}")
            raise SharePointConnectionError(f"API request failed: {exc}") from exc
    
    def post(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a POST request.
        
        Args:
            endpoint: API endpoint path
            data: Request body
            
        Returns:
            Response data
        """
        import requests
        
        url = f"{self.graphql_endpoint}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            logger.error(f"POST {url} failed: {exc}")
            if hasattr(exc, 'response') and exc.response is not None:
                logger.error(f"Response: {exc.response.text}")
            raise SharePointConnectionError(f"API request failed: {exc}") from exc
    
    def put(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a PUT request.
        
        Args:
            endpoint: API endpoint path
            data: Request body
            
        Returns:
            Response data
        """
        import requests
        
        url = f"{self.graphql_endpoint}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        
        try:
            response = requests.put(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as exc:
            logger.error(f"PUT {url} failed: {exc}")
            if hasattr(exc, 'response') and exc.response is not None:
                logger.error(f"Response: {exc.response.text}")
            raise SharePointConnectionError(f"API request failed: {exc}") from exc
    
    def delete(self, endpoint: str) -> bool:
        """Execute a DELETE request.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            True if successful
        """
        import requests
        
        url = f"{self.graphql_endpoint}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }
        
        try:
            response = requests.delete(url, headers=headers, timeout=30)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as exc:
            logger.error(f"DELETE {url} failed: {exc}")
            if hasattr(exc, 'response') and exc.response is not None:
                logger.error(f"Response: {exc.response.text}")
            raise SharePointConnectionError(f"API request failed: {exc}") from exc
    
    def download(self, endpoint: str) -> bytes:
        """Download binary content.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Binary content
        """
        import requests
        
        url = f"{self.graphql_endpoint}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as exc:
            logger.error(f"Download failed: {exc}")
            raise SharePointConnectionError(f"Download failed: {exc}") from exc
    
    def upload(self, endpoint: str, content: bytes) -> dict[str, Any]:
        """Upload binary content.
        
        Args:
            endpoint: API endpoint path
            content: Binary content to upload
            
        Returns:
            Response data
        """
        import requests
        
        url = f"{self.graphql_endpoint}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/octet-stream",
        }
        
        try:
            response = requests.put(url, headers=headers, data=content, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            logger.error(f"Upload failed: {exc}")
            if hasattr(exc, 'response') and exc.response is not None:
                logger.error(f"Response: {exc.response.text}")
            raise SharePointConnectionError(f"Upload failed: {exc}") from exc
    
    def __repr__(self) -> str:
        return f"GraphQLClient(site={self.site_url})"


def create_graphql_client(settings) -> GraphQLClient:
    """Create a Microsoft Graph GraphQL client.
    
    Args:
        settings: Application settings
        
    Returns:
        Authenticated GraphQL client
    """
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
        client = GraphQLClient(access_token, settings.shp_site_url)
        
        logger.info("Microsoft Graph GraphQL client initialized for %s", settings.shp_site_url)
        return client
        
    except Exception as exc:
        msg = f"Failed to create GraphQL client: {exc}"
        logger.error(msg)
        raise SharePointConnectionError(msg) from exc
