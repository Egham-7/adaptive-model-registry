"""
Update functions for endpoint tables.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import LLMModel, ModelEndpoint
from ..models.openrouter import OpenRouterModelWithEndpoints
from ..models.zdr import ZDREndpoint

logger = logging.getLogger(__name__)


async def update_existing_endpoints(
    session: AsyncSession,
    models: list[OpenRouterModelWithEndpoints],
    zdr_lookup: dict[tuple[str, str, str], ZDREndpoint],
) -> int:
    """Update existing endpoints with new data from OpenRouter and ZDR"""
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

        for ep in m.providers:
            # Check if endpoint exists
            result = await session.execute(
                select(ModelEndpoint).where(
                    ModelEndpoint.model_id == model_id,
                    ModelEndpoint.name == ep.name,
                    ModelEndpoint.provider_name == ep.provider_name,
                    ModelEndpoint.tag == ep.tag,
                )
            )
            db_endpoint = result.scalar_one_or_none()

            if db_endpoint is None:
                continue  # Skip if endpoint doesn't exist

            # Update endpoint fields if they have meaningful values
            updated = False

            if ep.context_length and (db_endpoint.context_length is None or db_endpoint.context_length == 0):  # type: ignore
                db_endpoint.context_length = ep.context_length  # type: ignore
                updated = True

            if ep.quantization and (not db_endpoint.quantization or db_endpoint.quantization == ""):  # type: ignore
                db_endpoint.quantization = ep.quantization  # type: ignore
                updated = True

            if ep.max_completion_tokens is not None and (db_endpoint.max_completion_tokens is None):  # type: ignore
                db_endpoint.max_completion_tokens = ep.max_completion_tokens  # type: ignore
                updated = True

            if ep.max_prompt_tokens is not None and (db_endpoint.max_prompt_tokens is None):  # type: ignore
                db_endpoint.max_prompt_tokens = ep.max_prompt_tokens  # type: ignore
                updated = True

            # Always update status and supports_implicit_caching to latest
            db_endpoint.status = ep.status  # type: ignore
            db_endpoint.supports_implicit_caching = "true" if ep.supports_implicit_caching else "false"  # type: ignore
            updated = True

            # Check if this endpoint is ZDR-enabled
            zdr_key = (ep.provider_name, ep.model_name, ep.tag)
            if zdr_key in zdr_lookup:
                db_endpoint.is_zdr = "true"  # type: ignore
                updated = True
            else:
                db_endpoint.is_zdr = "false"  # type: ignore

            if updated:
                updated_count += 1

    if updated_count > 0:
        await session.commit()
        logger.info(f"✓ Updated {updated_count} existing endpoints")

    return updated_count
