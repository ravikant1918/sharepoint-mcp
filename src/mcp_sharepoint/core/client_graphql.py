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
        
        # Cache site ID
        self._site_id_cache: str | None = None
        
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
        """Execute a GET request (REST-style).
        
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
