"""
Update functions for LLM models table.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import LLMModel
from ..models.openrouter import OpenRouterModelWithEndpoints

logger = logging.getLogger(__name__)


async def update_existing_llm_models(
    session: AsyncSession, models: list[OpenRouterModelWithEndpoints]
) -> int:
    """Update existing LLM models with new data from OpenRouter"""
    updated_count = 0

    for m in models:
        # Check if model exists
        result = await session.execute(
            select(LLMModel).where(
                LLMModel.author == m.author, LLMModel.model_name == m.model_name
            )
        )
        db_model = result.scalar_one_or_none()

        if db_model is None:
            continue  # Skip if model doesn't exist

        # Update fields if they have meaningful values
        updated = False

        if m.name and (not db_model.display_name or db_model.display_name == ""):  # type: ignore
            db_model.display_name = m.name  # type: ignore
            updated = True

        if m.description and (not db_model.description or db_model.description == ""):  # type: ignore
            db_model.description = m.description  # type: ignore
            updated = True

        if m.context_length and (db_model.context_length is None or db_model.context_length == 0):  # type: ignore
            db_model.context_length = m.context_length  # type: ignore
            updated = True

        if updated:
            db_model.last_updated = datetime.now(UTC)  # type: ignore
            updated_count += 1

    if updated_count > 0:
        await session.commit()
        logger.info(f"✓ Updated {updated_count} existing LLM models")

    return updated_count
