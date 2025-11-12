"""
Update functions for provider tables.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import LLMModel, ModelTopProvider
from ..models.openrouter import OpenRouterModelWithEndpoints

logger = logging.getLogger(__name__)


async def update_existing_top_provider(
    session: AsyncSession, models: list[OpenRouterModelWithEndpoints]
) -> int:
    """Update existing top provider metadata with new data from OpenRouter"""
    updated_count = 0

    for m in models:
        # Get model ID
        result = await session.execute(
            select(LLMModel.id).where(
                LLMModel.author == m.author, LLMModel.model_name == m.model_name
            )
        )
        model_id_row = result.scalar_one_or_none()

        if model_id_row is None:
            continue

        model_id = model_id_row

        # Check if top provider exists
        result = await session.execute(
            select(ModelTopProvider).where(ModelTopProvider.model_id == model_id)
        )
        db_top_provider = result.scalar_one_or_none()

        if db_top_provider is None:
            continue  # Skip if top provider doesn't exist

        # Update top provider fields (always update to latest)
        updated = False

        if m.top_provider.context_length is not None:
            db_top_provider.context_length = m.top_provider.context_length  # type: ignore
            updated = True

        if m.top_provider.max_completion_tokens is not None:
            db_top_provider.max_completion_tokens = m.top_provider.max_completion_tokens  # type: ignore
            updated = True

        # Always update is_moderated to latest value
        db_top_provider.is_moderated = "true" if m.top_provider.is_moderated else "false"  # type: ignore
        updated = True

        if updated:
            updated_count += 1

    if updated_count > 0:
        await session.commit()
        logger.info(
            f"✓ Updated top provider metadata for {updated_count} existing models"
        )

    return updated_count
