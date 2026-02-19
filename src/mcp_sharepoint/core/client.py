"""SharePoint client factory.

Provides a cached ``ClientContext`` ready for use by service layer modules.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext

from ..config import get_settings
from ..exceptions import SharePointConnectionError

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_sp_context() -> ClientContext:
    """Return a cached, authenticated SharePoint ``ClientContext``.

    Raises:
        SharePointConnectionError: if the context cannot be established.
    """
    settings = get_settings()
    try:
        credentials = ClientCredential(settings.shp_id_app, settings.shp_id_app_secret)
        ctx = ClientContext(settings.shp_site_url).with_credentials(credentials)
        logger.info("SharePoint client context initialised for %s", settings.shp_site_url)
        return ctx
    except Exception as exc:
        msg = f"Failed to create SharePoint context: {exc}"
        logger.error(msg)
        raise SharePointConnectionError(msg) from exc
