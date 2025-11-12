"""
OpenRouter API fetching utilities.
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from ..models.openrouter import (
    Endpoint,
    OpenRouterModel,
    OpenRouterModelWithEndpoints,
    parse_openrouter_model,
)
from .cache import (
    OPENROUTER_API_BASE,
    load_cached_endpoints,
    load_cached_models,
    save_endpoints_to_cache,
    save_models_to_cache,
)

logger = logging.getLogger(__name__)


async def fetch_openrouter_models(use_cache: bool = True) -> list[OpenRouterModel]:
    """
    Fetch all models from OpenRouter API (async) and parse into Pydantic models.
    Uses 24-hour cache by default to avoid unnecessary API calls.
    """
    # Try to load from cache first
    if use_cache:
        cached_raw = load_cached_models()
        if cached_raw is not None:
            models = [
                parsed_model
                for raw_model in cached_raw
                if (parsed_model := parse_openrouter_model(raw_model)) is not None
            ]
            return models

    # Fetch from API
    url = "https://openrouter.ai/api/v1/models"
    logger.info(f"Fetching models from {url}")

    async with httpx.AsyncClient(
        timeout=30.0, limits=httpx.Limits(max_connections=100)
    ) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            raw_models: list[dict[str, Any]] = data.get("data", [])

            # Save to cache
            if use_cache:
                save_models_to_cache(raw_models)

            # Parse into Pydantic models for strict typing using comprehension
            models = [
                parsed_model
                for raw_model in raw_models
                if (parsed_model := parse_openrouter_model(raw_model)) is not None
            ]

            logger.info(f"✓ Fetched and parsed {len(models)} models from OpenRouter")
            return models
        except httpx.HTTPError as e:
            logger.error(f"❌ Failed to fetch models: {e}")
            sys.exit(1)


def parse_provider_model(model_id: str) -> tuple[Optional[str], Optional[str]]:
    """Parse provider/model_name from OpenRouter model ID"""
    if "/" not in model_id:
        return None, None

    parts = model_id.split("/", 1)
    provider = parts[0].lower()
    model_name = parts[1]

    # Normalize specific Claude model names
    model_name = normalize_model_name(model_name)

    return provider, model_name


def normalize_model_name(model_name: str) -> str:
    """Normalize specific Claude model names by replacing dots with dashes"""
    if model_name in ["claude-sonnet-4.5", "claude-haiku-4.5", "claude-opus-4.1"]:
        return model_name.replace(".", "-")
    return model_name


async def fetch_model_endpoints(
    client: httpx.AsyncClient, model: OpenRouterModel, use_cache: bool = True
) -> Optional[OpenRouterModelWithEndpoints]:
    """
    Fetch endpoints for a model from OpenRouter API with caching.
    Returns None if endpoints cannot be fetched.
    """
    # Try to load from cache first
    cached_data = None
    if use_cache:
        cached_data = load_cached_endpoints(model.id)

    # If cache miss, fetch from API
    if cached_data is None:
        url = f"{OPENROUTER_API_BASE}/models/{model.id}/endpoints"

        try:
            response = await client.get(url)
            response.raise_for_status()
            cached_data = response.json().get("data", {})

            # Save to cache
            if use_cache:
                save_endpoints_to_cache(model.id, cached_data)

        except httpx.HTTPError as e:
            logger.warning(f"Failed to fetch endpoints for {model.id}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error fetching endpoints for {model.id}: {e}")
            return None

    # Parse cached/fetched data
    try:
        # Parse endpoints
        endpoints_data = cached_data.get("endpoints", [])
        endpoints = [Endpoint(**ep) for ep in endpoints_data]

        # Parse author/model_name
        author, model_name = parse_provider_model(model.id)
        if not author or not model_name:
            logger.warning(f"Could not parse author/model from {model.id}")
            return None

        # Convert timestamp
        created_at = datetime.fromtimestamp(model.created, tz=timezone.utc)

        return OpenRouterModelWithEndpoints(
            openrouter_id=model.id,
            name=model.name,
            description=model.description,
            context_length=model.context_length,
            pricing=model.pricing,
            architecture=model.architecture,
            top_provider=model.top_provider,
            created=model.created,
            supported_parameters=model.supported_parameters,
            default_parameters=model.default_parameters,
            providers=endpoints,
            author=author,
            model_name=model_name,
            created_at=created_at,
        )
    except Exception as e:
        logger.warning(f"Error processing endpoints data for {model.id}: {e}")
        return None


async def fetch_all_endpoints_parallel(
    models: list[OpenRouterModel], use_cache: bool = True
) -> list[OpenRouterModelWithEndpoints]:
    """Fetch endpoints for all models in parallel with caching"""
    # Create a single client for all requests
    async with httpx.AsyncClient(
        timeout=30.0, limits=httpx.Limits(max_connections=100)
    ) as client:
        # Run all endpoint fetches concurrently (with caching)
        results = await asyncio.gather(
            *[fetch_model_endpoints(client, model, use_cache) for model in models]
        )

    # Count cache hits for logging
    if use_cache:
        cache_hits = sum(
            1 for model in models if load_cached_endpoints(model.id) is not None
        )
        cache_misses = len(models) - cache_hits
        logger.info(f"  • Cache: {cache_hits} hits, {cache_misses} misses")

    # Filter out None values
    return [m for m in results if m is not None]