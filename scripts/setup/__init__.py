"""
OpenRouter Model Registry Setup Package

This package provides a modular pipeline for syncing OpenRouter models
to a PostgreSQL database with full ZDR (Zero Downtime Routing) support.
"""

import argparse
import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from .fetchers.openrouter import fetch_all_endpoints_parallel, fetch_openrouter_models
from .fetchers.zdr import fetch_zdr_endpoints
from .inserters.bulk_insert import bulk_insert_models
from .models.database import Base, SyncMetadata
from .models.openrouter import OpenRouterModelWithEndpoints
from .models.zdr import ZDREndpoint
from .updaters.architecture import (
    update_existing_architecture_modalities,
    update_existing_model_architecture,
)
from .updaters.endpoints import update_existing_endpoints
from .updaters.llm_models import update_existing_llm_models
from .updaters.parameters import (
    update_existing_default_parameters,
    update_existing_supported_parameters,
)
from .updaters.pricing import (
    update_existing_endpoint_pricing,
    update_existing_model_pricing,
)
from .updaters.providers import update_existing_top_provider
from .utils.exports import save_to_polars
from .utils.validation import validate_parameter_constants

# Re-export key types for package users
__all__ = [
    "OpenRouterModelWithEndpoints",
    "ZDREndpoint",
]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def should_sync(
    session: AsyncSession, sync_type: str, max_age_hours: int = 24
) -> bool:
    """Check if we need to sync based on last sync time"""
    result = await session.execute(
        select(SyncMetadata)
        .where(SyncMetadata.sync_type == sync_type)
        .order_by(SyncMetadata.last_sync_at.desc())
        .limit(1)
    )
    last_sync = result.scalar_one_or_none()

    if not last_sync:
        logger.info(f"Never synced {sync_type} before, will sync now")
        return True  # Never synced before

    age_hours = (
        datetime.now(timezone.utc) - last_sync.last_sync_at
    ).total_seconds() / 3600

    if age_hours >= max_age_hours:
        logger.info(
            f"{sync_type} data is {age_hours:.1f} hours old (max: {max_age_hours}h), will sync"
        )
        return True

    logger.info(f"{sync_type} data is {age_hours:.1f} hours old, skipping sync")
    return False


async def main_async(
    db_url: str,
    output_json: Optional[str] = None,
    output_parquet: Optional[str] = None,
    output_csv: Optional[str] = None,
    force_refresh: bool = False,
) -> None:
    """Main async pipeline using SQLAlchemy ORM"""
    # Validate parameter constants on startup
    validate_parameter_constants()

    logger.info("🚀 Starting OpenRouter model sync pipeline")

    # Connect to PostgreSQL early to check sync status
    logger.info("Connecting to PostgreSQL...")
    async_db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(
        async_db_url, echo=False, pool_size=10, max_overflow=20
    )

    # Create tables (including new SyncMetadata table)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✓ Database tables created/verified")

    # Create session factory
    async_session = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    # Check if we need to sync OpenRouter models
    should_sync_models = force_refresh
    if not force_refresh:
        async with async_session() as session:
            should_sync_models = await should_sync(session, "openrouter_models")

    raw_models = []
    models_with_endpoints = []
    zdr_lookup = {}

    if should_sync_models:
        # Step 1: Fetch models from OpenRouter
        logger.info("Fetching OpenRouter models...")
        raw_models = await fetch_openrouter_models(
            use_cache=False
        )  # Always fresh for sync

        # Step 2: Fetch endpoints for all models in parallel
        logger.info(f"Fetching endpoints for {len(raw_models)} models in parallel...")
        models_with_endpoints = await fetch_all_endpoints_parallel(
            raw_models, use_cache=False  # Always fresh for sync
        )
        logger.info(
            f"✓ Fetched endpoints for {len(models_with_endpoints)} models (from {len(raw_models)} total)"
        )

        # Step 2.5: Fetch ZDR endpoints
        logger.info("Fetching ZDR endpoints...")
        zdr_lookup = await fetch_zdr_endpoints(use_cache=False)  # Always fresh for sync
        logger.info(f"✓ Fetched {len(zdr_lookup)} ZDR endpoints")

        # Record sync metadata
        async with async_session() as session:
            # Upsert OpenRouter models sync metadata
            sync_metadata = SyncMetadata(
                sync_type="openrouter_models",
                last_sync_at=datetime.now(timezone.utc),
                models_count=len(models_with_endpoints),
            )
            await session.merge(sync_metadata)

            # Upsert ZDR endpoints sync metadata
            zdr_sync_metadata = SyncMetadata(
                sync_type="zdr_endpoints",
                last_sync_at=datetime.now(timezone.utc),
                zdr_endpoints_count=len(zdr_lookup),
            )
            await session.merge(zdr_sync_metadata)

            await session.commit()

        logger.info("✓ Sync metadata recorded")
    else:
        logger.info("⏭️  Skipping API calls - using existing database data")
        # If not syncing, we still need to load data from database for updates
        # This is handled by the update functions below

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

    # Database connection already established above

    # Step 5: Update existing models with new data
    logger.info("Updating existing models with new data...")
    async with async_session() as session:
        # Update existing models in all tables
        updated_llm = await update_existing_llm_models(session, models_with_endpoints)
        updated_pricing = await update_existing_model_pricing(
            session, models_with_endpoints
        )
        updated_architecture = await update_existing_model_architecture(
            session, models_with_endpoints
        )
        updated_modalities = await update_existing_architecture_modalities(
            session, models_with_endpoints
        )
        updated_top_provider = await update_existing_top_provider(
            session, models_with_endpoints
        )
        updated_endpoints = await update_existing_endpoints(
            session, models_with_endpoints, zdr_lookup
        )
        updated_endpoint_pricing = await update_existing_endpoint_pricing(
            session, models_with_endpoints, zdr_lookup
        )
        updated_supported_params = await update_existing_supported_parameters(
            session, models_with_endpoints
        )
        updated_default_params = await update_existing_default_parameters(
            session, models_with_endpoints
        )

    logger.info("✓ Updates complete:")
    logger.info(f"  • LLM models: {updated_llm}")
    logger.info(f"  • Model pricing: {updated_pricing}")
    logger.info(f"  • Architecture: {updated_architecture}")
    logger.info(f"  • Architecture modalities: {updated_modalities}")
    logger.info(f"  • Top provider: {updated_top_provider}")
    logger.info(f"  • Endpoints: {updated_endpoints}")
    logger.info(f"  • Endpoint pricing: {updated_endpoint_pricing}")
    logger.info(f"  • Supported parameters: {updated_supported_params}")
    logger.info(f"  • Default parameters: {updated_default_params}")

    # Step 6: Insert new models
    logger.info("Inserting new models to database...")
    async with async_session() as session:
        inserted, skipped = await bulk_insert_models(
            session, models_with_endpoints, zdr_lookup
        )

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
        "--force-refresh",
        action="store_true",
        help="Force refresh data from OpenRouter API (ignore sync timestamps)",
    )
    args = parser.parse_args()

    # Run async main with asyncio
    asyncio.run(
        main_async(
            args.db_url,
            args.output_json,
            args.output_parquet,
            args.output_csv,
            args.force_refresh,
        )
    )


if __name__ == "__main__":
    main()
