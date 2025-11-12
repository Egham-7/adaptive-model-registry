"""
ZDR endpoint fetching utilities.
"""

import logging
import sys
from typing import Any

import httpx

from ..models.zdr import ZDREndpoint
from .cache import OPENROUTER_API_BASE, load_cached_zdr_endpoints, save_zdr_endpoints_to_cache

logger = logging.getLogger(__name__)


async def fetch_zdr_endpoints(use_cache: bool = True) -> dict[tuple[str, str, str], ZDREndpoint]:
    """
    Fetch ZDR endpoints from OpenRouter API with caching.
    Returns a lookup dict keyed by (provider_name, model_name, tag).
    """
    # Try to load from cache first
    if use_cache:
        cached_raw = load_cached_zdr_endpoints()
        if cached_raw is not None:
            zdr_lookup = {}
            for raw_endpoint in cached_raw:
                try:
                    endpoint = ZDREndpoint(**raw_endpoint)
                    key = (endpoint.provider_name, endpoint.model_name, endpoint.tag)
                    zdr_lookup[key] = endpoint
                except Exception as e:
                    logger.warning(f"Failed to parse cached ZDR endpoint: {e}")
            return zdr_lookup

    # Fetch from API
    url = f"{OPENROUTER_API_BASE}/endpoints/zdr"
    logger.info(f"Fetching ZDR endpoints from {url}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            raw_endpoints: list[dict[str, Any]] = data.get("data", [])

            # Save to cache
            if use_cache:
                save_zdr_endpoints_to_cache(raw_endpoints)

            # Parse into lookup dict
            zdr_lookup = {}
            for raw_endpoint in raw_endpoints:
                try:
                    endpoint = ZDREndpoint(**raw_endpoint)
                    key = (endpoint.provider_name, endpoint.model_name, endpoint.tag)
                    zdr_lookup[key] = endpoint
                except Exception as e:
                    logger.warning(f"Failed to parse ZDR endpoint {raw_endpoint}: {e}")

            logger.info(f"✓ Fetched and parsed {len(zdr_lookup)} ZDR endpoints from OpenRouter")
            return zdr_lookup

        except httpx.HTTPError as e:
            logger.error(f"❌ Failed to fetch ZDR endpoints: {e}")
            sys.exit(1)