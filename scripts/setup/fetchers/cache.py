"""
Caching utilities for OpenRouter API data.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# OpenRouter API base URL
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"


def get_cache_dir() -> Path:
    """Get cache directory for OpenRouter data"""
    cache_dir = Path.home() / ".cache" / "adaptive_router"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_models_cache_path() -> Path:
    """Get cache file path for OpenRouter models list"""
    return get_cache_dir() / "openrouter_models.json"


def get_endpoints_cache_dir() -> Path:
    """Get cache directory for model endpoints"""
    endpoints_dir = get_cache_dir() / "endpoints"
    endpoints_dir.mkdir(parents=True, exist_ok=True)
    return endpoints_dir


def get_endpoint_cache_path(model_id: str) -> Path:
    """Get cache file path for a specific model's endpoints"""
    # Replace / with _ for filesystem safety
    safe_id = model_id.replace("/", "_")
    return get_endpoints_cache_dir() / f"{safe_id}.json"


def get_zdr_cache_path() -> Path:
    """Get cache file path for ZDR endpoints"""
    return get_cache_dir() / "zdr_endpoints.json"


def load_cached_models() -> Optional[list[dict[str, Any]]]:
    """Load cached OpenRouter models if fresh (less than 24 hours old)"""
    cache_path = get_models_cache_path()

    if not cache_path.exists():
        return None

    # Check if cache is fresh (less than 24 hours old)
    cache_age_hours = (
        datetime.now(timezone.utc).timestamp() - cache_path.stat().st_mtime
    ) / 3600

    if cache_age_hours > 24:
        logger.info(f"Models cache is {cache_age_hours:.1f} hours old, will refresh")
        return None

    try:
        with open(cache_path, "r") as f:
            data = json.load(f)
            logger.info(
                f"✓ Loaded {len(data)} models from cache (age: {cache_age_hours:.1f}h)"
            )
            return data
    except Exception as e:
        logger.warning(f"Failed to load models cache: {e}")
        return None


def save_models_to_cache(models: list[dict[str, Any]]) -> None:
    """Save OpenRouter models to cache"""
    cache_path = get_models_cache_path()

    try:
        with open(cache_path, "w") as f:
            json.dump(models, f)
        logger.info(f"✓ Saved {len(models)} models to cache: {cache_path}")
    except Exception as e:
        logger.warning(f"Failed to save models cache: {e}")


def load_cached_endpoints(model_id: str) -> Optional[dict[str, Any]]:
    """Load cached endpoints for a model if fresh (less than 24 hours old)"""
    cache_path = get_endpoint_cache_path(model_id)

    if not cache_path.exists():
        return None

    # Check if cache is fresh (less than 24 hours old)
    cache_age_hours = (
        datetime.now(timezone.utc).timestamp() - cache_path.stat().st_mtime
    ) / 3600

    if cache_age_hours > 24:
        return None

    try:
        with open(cache_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.debug(f"Failed to load endpoints cache for {model_id}: {e}")
        return None


def save_endpoints_to_cache(model_id: str, endpoints_data: dict[str, Any]) -> None:
    """Save model endpoints to cache"""
    cache_path = get_endpoint_cache_path(model_id)

    try:
        with open(cache_path, "w") as f:
            json.dump(endpoints_data, f)
    except Exception as e:
        logger.debug(f"Failed to save endpoints cache for {model_id}: {e}")


def load_cached_zdr_endpoints() -> Optional[list[dict[str, Any]]]:
    """Load cached ZDR endpoints if fresh (less than 24 hours old)"""
    cache_path = get_zdr_cache_path()

    if not cache_path.exists():
        return None

    # Check if cache is fresh (less than 24 hours old)
    cache_age_hours = (
        datetime.now(timezone.utc).timestamp() - cache_path.stat().st_mtime
    ) / 3600

    if cache_age_hours > 24:
        logger.info(f"ZDR endpoints cache is {cache_age_hours:.1f} hours old, will refresh")
        return None

    try:
        with open(cache_path, "r") as f:
            data = json.load(f)
            logger.info(
                f"✓ Loaded {len(data)} ZDR endpoints from cache (age: {cache_age_hours:.1f}h)"
            )
            return data
    except Exception as e:
        logger.warning(f"Failed to load ZDR endpoints cache: {e}")
        return None


def save_zdr_endpoints_to_cache(zdr_endpoints: list[dict[str, Any]]) -> None:
    """Save ZDR endpoints to cache"""
    cache_path = get_zdr_cache_path()

    try:
        with open(cache_path, "w") as f:
            json.dump(zdr_endpoints, f)
        logger.info(f"✓ Saved {len(zdr_endpoints)} ZDR endpoints to cache: {cache_path}")
    except Exception as e:
        logger.warning(f"Failed to save ZDR endpoints cache: {e}")