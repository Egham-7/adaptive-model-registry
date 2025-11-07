#!/usr/bin/env python3
"""
OpenRouter Model Sync Pipeline

Fetches models from OpenRouter API with endpoints data and syncs to PostgreSQL.

High-performance async implementation using asyncio, httpx, and SQLAlchemy ORM.

Usage:
    python scripts/sync_openrouter_models.py --db-url postgresql://user:pass@host:5432/dbname

Dependencies:
    pip install httpx asyncio sqlalchemy[asyncio] asyncpg pydantic polars
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
import polars as pl
from pydantic import BaseModel, Field
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# SQLAlchemy Base
class Base(DeclarativeBase):
    pass


# ============================================================================
# NORMALIZED SQLALCHEMY MODELS
# ============================================================================


class LLMModel(Base):
    """Core model table with basic metadata"""

    __tablename__ = "llm_models"
    __table_args__ = (
        UniqueConstraint("author", "model_name", name="uq_author_model"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Author and model name form the composite unique identifier
    author = Column(String(50), nullable=False, index=True)
    model_name = Column(String(255), nullable=False, index=True)

    # Basic metadata
    display_name = Column(String(255))
    description = Column(Text)
    context_length = Column(Integer)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    last_updated = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ModelPricing(Base):
    """Model pricing information (one-to-one with LLMModel)"""

    __tablename__ = "model_pricing"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )

    # Pricing in USD per token (using NUMERIC for precision)
    prompt_cost = Column(String(50), nullable=False)  # Keep as string for precision
    completion_cost = Column(String(50), nullable=False)
    request_cost = Column(String(50), nullable=False, default="0")
    image_cost = Column(String(50), nullable=False, default="0")
    web_search_cost = Column(String(50), nullable=False, default="0")
    internal_reasoning_cost = Column(String(50), nullable=False, default="0")


class ModelArchitecture(Base):
    """Model architecture metadata (one-to-one with LLMModel)"""

    __tablename__ = "model_architecture"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )

    modality = Column(String(50), nullable=False)
    tokenizer = Column(String(100), nullable=False)
    instruct_type = Column(String(50))


class ModelArchitectureModality(Base):
    """Input/output modalities for model architecture (many-to-one with ModelArchitecture)"""

    __tablename__ = "model_architecture_modalities"
    __table_args__ = (
        UniqueConstraint(
            "architecture_id",
            "modality_type",
            "modality_value",
            name="uq_arch_modality",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    architecture_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    # 'input' or 'output'
    modality_type = Column(String(10), nullable=False)
    modality_value = Column(String(50), nullable=False)


class ModelTopProvider(Base):
    """Top provider metadata (one-to-one with LLMModel)"""

    __tablename__ = "model_top_provider"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )

    context_length = Column(Integer)
    max_completion_tokens = Column(Integer)
    is_moderated = Column(String(10), nullable=False, default="false")


class ModelEndpoint(Base):
    """Model endpoint information (one-to-many with LLMModel)"""

    __tablename__ = "model_endpoints"
    __table_args__ = (
        UniqueConstraint(
            "model_id", "name", "provider_name", "tag", name="uq_model_endpoint"
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    name = Column(String(255), nullable=False)
    endpoint_model_name = Column(String(255), nullable=False)
    context_length = Column(Integer, nullable=False)
    provider_name = Column(String(100), nullable=False, index=True)
    tag = Column(String(100), nullable=False)
    quantization = Column(String(50))
    max_completion_tokens = Column(Integer)
    max_prompt_tokens = Column(Integer)
    status = Column(Integer, nullable=False)
    uptime_last_30m = Column(String(50))
    supports_implicit_caching = Column(String(10), nullable=False, default="false")


class ModelEndpointPricing(Base):
    """Endpoint-specific pricing (one-to-one with ModelEndpoint)"""

    __tablename__ = "model_endpoint_pricing"

    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint_id = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )

    prompt_cost = Column(String(50), nullable=False, default="0")
    completion_cost = Column(String(50), nullable=False, default="0")
    request_cost = Column(String(50), nullable=False, default="0")
    image_cost = Column(String(50), nullable=False, default="0")


class ModelSupportedParameter(Base):
    """Supported parameters for model (many-to-many with LLMModel)"""

    __tablename__ = "model_supported_parameters"
    __table_args__ = (
        UniqueConstraint("model_id", "parameter_name", name="uq_model_parameter"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    parameter_name = Column(String(100), nullable=False)


class ModelDefaultParameters(Base):
    """Default parameters for model (one-to-one with LLMModel, stored as JSON for flexibility)"""

    __tablename__ = "model_default_parameters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )

    parameters = Column(JSON)


# OpenRouter API base URL
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"


class Architecture(BaseModel):
    """Model architecture details"""

    modality: str
    input_modalities: list[str]
    output_modalities: list[str]
    tokenizer: str
    instruct_type: Optional[str] = None


class Pricing(BaseModel):
    """Model pricing in USD per token"""

    prompt: str
    completion: str
    request: str = "0"
    image: str = "0"
    web_search: str = "0"
    internal_reasoning: str = "0"


class TopProvider(BaseModel):
    """Top provider metadata"""

    context_length: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    is_moderated: bool = False


class OpenRouterModel(BaseModel):
    """OpenRouter API model response with strict typing"""

    id: str
    canonical_slug: str
    name: str
    description: str
    context_length: int
    pricing: Pricing
    architecture: Architecture
    top_provider: TopProvider
    created: int
    supported_parameters: list[str]
    default_parameters: Optional[dict[str, Any]] = None


class Endpoint(BaseModel):
    """OpenRouter endpoint information"""

    name: str
    model_name: str
    context_length: int
    pricing: dict[str, Any]
    provider_name: str
    tag: str
    quantization: Optional[str] = None
    max_completion_tokens: Optional[int] = None
    max_prompt_tokens: Optional[int] = None
    supported_parameters: list[str]
    status: int
    uptime_last_30m: Optional[float] = None
    supports_implicit_caching: bool


class OpenRouterModelWithEndpoints(BaseModel):
    """OpenRouter model with endpoints data"""

    # OpenRouter ID (e.g., "google/gemini-2.5-pro")
    openrouter_id: str

    # OpenRouter fields
    name: str
    description: str
    context_length: int
    pricing: Pricing
    architecture: Architecture
    top_provider: TopProvider
    created: int
    supported_parameters: list[str]
    default_parameters: Optional[dict[str, Any]] = None

    # Providers from /api/v1/models/{id}/endpoints
    providers: list[Endpoint]

    # Parsed author info
    author: str
    model_name: str

    # Metadata
    created_at: datetime
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def parse_openrouter_model(raw_model: dict[str, Any]) -> Optional[OpenRouterModel]:
    """Parse raw model dict into OpenRouterModel, return None if invalid"""
    try:
        return OpenRouterModel(**raw_model)
    except Exception as e:
        logger.warning(f"Failed to parse model {raw_model.get('id')}: {e}")
        return None


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


async def get_existing_models_from_db(session: AsyncSession) -> set[tuple[str, str]]:
    """Get existing (author, model_name) tuples from database"""
    result = await session.execute(select(LLMModel.author, LLMModel.model_name))
    return {(row[0], row[1]) for row in result.all()}


async def bulk_insert_models(
    session: AsyncSession, models: list[OpenRouterModelWithEndpoints]
) -> tuple[int, int]:
    """
    Bulk insert models using normalized schema with SQLAlchemy ORM.
    Only inserts new models, skips existing ones.

    Returns: (inserted_count, skipped_count)
    """
    # Get existing models
    existing = await get_existing_models_from_db(session)
    new_models = [m for m in models if (m.author, m.model_name) not in existing]
    skipped = len(models) - len(new_models)

    if not new_models:
        logger.info("No new models to insert")
        return 0, skipped

    inserted_count = 0

    for m in new_models:
        try:
            # 1. Insert core model
            db_model = LLMModel(
                author=m.author,
                model_name=m.model_name,
                display_name=m.name,
                description=m.description,
                context_length=m.context_length,
                created_at=m.created_at,
                last_updated=m.last_updated,
            )
            session.add(db_model)
            await session.flush()  # Get the ID

            model_id = db_model.id

            # 2. Insert pricing
            pricing = ModelPricing(
                model_id=model_id,
                prompt_cost=m.pricing.prompt,
                completion_cost=m.pricing.completion,
                request_cost=m.pricing.request,
                image_cost=m.pricing.image,
                web_search_cost=m.pricing.web_search,
                internal_reasoning_cost=m.pricing.internal_reasoning,
            )
            session.add(pricing)

            # 3. Insert architecture
            architecture = ModelArchitecture(
                model_id=model_id,
                modality=m.architecture.modality,
                tokenizer=m.architecture.tokenizer,
                instruct_type=m.architecture.instruct_type,
            )
            session.add(architecture)
            await session.flush()  # Get architecture ID

            architecture_id = architecture.id

            # 4. Insert architecture modalities
            for input_mod in m.architecture.input_modalities:
                modality = ModelArchitectureModality(
                    architecture_id=architecture_id,
                    modality_type="input",
                    modality_value=input_mod,
                )
                session.add(modality)

            for output_mod in m.architecture.output_modalities:
                modality = ModelArchitectureModality(
                    architecture_id=architecture_id,
                    modality_type="output",
                    modality_value=output_mod,
                )
                session.add(modality)

            # 5. Insert top provider
            top_provider = ModelTopProvider(
                model_id=model_id,
                context_length=m.top_provider.context_length,
                max_completion_tokens=m.top_provider.max_completion_tokens,
                is_moderated=str(m.top_provider.is_moderated).lower(),
            )
            session.add(top_provider)

            # 6. Insert supported parameters
            for param in m.supported_parameters:
                supported_param = ModelSupportedParameter(
                    model_id=model_id, parameter_name=param
                )
                session.add(supported_param)

            # 7. Insert default parameters (if any)
            if m.default_parameters:
                default_params = ModelDefaultParameters(
                    model_id=model_id, parameters=m.default_parameters
                )
                session.add(default_params)

            # 8. Insert providers
            for ep in m.providers:
                # Check if endpoint already exists (handle OpenRouter API duplicates)
                existing_endpoint = await session.execute(
                    select(ModelEndpoint).where(
                        ModelEndpoint.model_id == model_id,
                        ModelEndpoint.name == ep.name,
                        ModelEndpoint.provider_name == ep.provider_name,
                        ModelEndpoint.tag == ep.tag,
                    )
                )
                existing_endpoint = existing_endpoint.scalar_one_or_none()

                if existing_endpoint:
                    endpoint = existing_endpoint
                else:
                    endpoint = ModelEndpoint(
                        model_id=model_id,
                        name=ep.name,
                        endpoint_model_name=ep.model_name,
                        context_length=ep.context_length,
                        provider_name=ep.provider_name,
                        tag=ep.tag,
                        quantization=ep.quantization,
                        max_completion_tokens=ep.max_completion_tokens,
                        max_prompt_tokens=ep.max_prompt_tokens,
                        status=ep.status,
                        uptime_last_30m=(
                            str(ep.uptime_last_30m) if ep.uptime_last_30m else None
                        ),
                        supports_implicit_caching=str(
                            ep.supports_implicit_caching
                        ).lower(),
                    )
                    session.add(endpoint)
                    await session.flush()  # Get endpoint ID

                    # 9. Insert endpoint pricing (only for new endpoints)
                    endpoint_pricing = ModelEndpointPricing(
                        endpoint_id=endpoint.id,
                        prompt_cost=ep.pricing.get("prompt", "0"),
                        completion_cost=ep.pricing.get("completion", "0"),
                        request_cost=ep.pricing.get("request", "0"),
                        image_cost=ep.pricing.get("image", "0"),
                    )
                    session.add(endpoint_pricing)

            inserted_count += 1

        except Exception as e:
            logger.error(f"Failed to insert model {m.openrouter_id}: {e}")
            await session.rollback()
            continue

    # Commit all changes
    await session.commit()

    logger.info(f"✓ Inserted {inserted_count} new models")
    return inserted_count, skipped


def save_to_polars(
    models: list[OpenRouterModelWithEndpoints],
    output_path: Path,
    format: str = "parquet",
) -> None:
    """Save models with endpoints to file using Polars (parquet, csv, or json)"""
    # Convert Pydantic models to dict records
    records = [
        {
            "openrouter_id": m.openrouter_id,
            "author": m.author,
            "model_name": m.model_name,
            "display_name": m.name,
            "description": m.description,
            "context_length": m.context_length,
            "prompt_cost_per_1m": float(m.pricing.prompt) * 1_000_000,
            "completion_cost_per_1m": float(m.pricing.completion) * 1_000_000,
            "max_completion_tokens": m.top_provider.max_completion_tokens,
            "is_moderated": m.top_provider.is_moderated,
            "supports_tools": "tools" in m.supported_parameters,
            "supports_vision": "image" in m.architecture.input_modalities,
            "num_providers": len(m.providers),
            "provider_providers": [ep.provider_name for ep in m.providers],
            "created_at": m.created_at,
            "last_updated": m.last_updated,
        }
        for m in models
    ]

    # Create Polars DataFrame
    df = pl.DataFrame(records)

    # Save based on format
    if format == "parquet":
        df.write_parquet(output_path)
    elif format == "csv":
        df.write_csv(output_path)
    elif format == "json":
        df.write_json(output_path)
    else:
        raise ValueError(f"Unsupported format: {format}")

    logger.info(f"✓ Saved {len(models)} models to {output_path} ({format} format)")
    logger.info(f"  • Dataset shape: {df.shape[0]} rows × {df.shape[1]} columns")


async def main_async(
    db_url: str,
    output_json: Optional[str] = None,
    output_parquet: Optional[str] = None,
    output_csv: Optional[str] = None,
    no_cache: bool = False,
) -> None:
    """Main async pipeline using SQLAlchemy ORM"""
    logger.info("🚀 Starting OpenRouter model sync pipeline")

    # Step 1: Fetch models from OpenRouter (with caching)
    raw_models = await fetch_openrouter_models(use_cache=not no_cache)

    # Step 2: Fetch endpoints for all models in parallel (with caching)
    logger.info(f"Fetching endpoints for {len(raw_models)} models in parallel...")
    models_with_endpoints = await fetch_all_endpoints_parallel(
        raw_models, use_cache=not no_cache
    )
    logger.info(
        f"✓ Fetched endpoints for {len(models_with_endpoints)} models (from {len(raw_models)} total)"
    )

    # Group by author for stats
    by_author: dict[str, int] = {}
    for model in models_with_endpoints:
        by_author[model.author] = by_author.get(model.author, 0) + 1

    logger.info("Models by author:")
    for author, count in sorted(by_author.items()):
        logger.info(f"  • {author}: {count} models")

    # Step 3: Optional exports
    if output_json:
        output_path = Path(output_json)
        with open(output_path, "w") as f:
            json.dump(
                [m.model_dump(mode="json") for m in models_with_endpoints],
                f,
                indent=2,
                default=str,
            )
        logger.info(f"✓ Saved models with endpoints to {output_path} (JSON)")

    if output_parquet:
        save_to_polars(models_with_endpoints, Path(output_parquet), format="parquet")

    if output_csv:
        save_to_polars(models_with_endpoints, Path(output_csv), format="csv")

    # Step 4: Connect to PostgreSQL with SQLAlchemy
    logger.info("Connecting to PostgreSQL...")
    # Convert postgresql:// to postgresql+asyncpg://
    async_db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(
        async_db_url, echo=False, pool_size=10, max_overflow=20
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✓ Database tables created/verified")

    # Create session factory
    async_session = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    # Step 5: Insert models
    logger.info("Syncing models to database...")
    async with async_session() as session:
        inserted, skipped = await bulk_insert_models(session, models_with_endpoints)

    logger.info("✓ Database sync complete:")
    logger.info(f"  • Inserted: {inserted} new models")
    logger.info(f"  • Skipped: {skipped} existing models")

    await engine.dispose()
    logger.info("✅ Pipeline completed successfully")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync OpenRouter models to PostgreSQL with optional dataset exports"
    )
    parser.add_argument(
        "--db-url",
        required=True,
        help="PostgreSQL connection URL (postgresql://user:pass@host:5432/dbname)",
    )
    parser.add_argument(
        "--output-json",
        help="Optional: Save enriched models to JSON file",
    )
    parser.add_argument(
        "--output-parquet",
        help="Optional: Save dataset to Parquet file (efficient columnar format)",
    )
    parser.add_argument(
        "--output-csv",
        help="Optional: Save dataset to CSV file",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Skip cache and fetch fresh data from OpenRouter API",
    )
    args = parser.parse_args()

    # Run async main with asyncio
    asyncio.run(
        main_async(
            args.db_url,
            args.output_json,
            args.output_parquet,
            args.output_csv,
            args.no_cache,
        )
    )


if __name__ == "__main__":
    main()
