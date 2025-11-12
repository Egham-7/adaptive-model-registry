"""
Update functions for pricing tables.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import (
    LLMModel,
    ModelEndpoint,
    ModelEndpointPricing,
    ModelPricing,
)
from ..models.openrouter import OpenRouterModelWithEndpoints
from ..models.zdr import ZDREndpoint

logger = logging.getLogger(__name__)


async def update_existing_model_pricing(
    session: AsyncSession, models: list[OpenRouterModelWithEndpoints]
) -> int:
    """Update existing model pricing with new data from OpenRouter"""
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

        # Check if pricing exists
        result = await session.execute(
            select(ModelPricing).where(ModelPricing.model_id == model_id)
        )
        db_pricing = result.scalar_one_or_none()

        if db_pricing is None:
            continue  # Skip if pricing doesn't exist

        # Update pricing fields if they have meaningful values
        updated = False

        if m.pricing.prompt and (not db_pricing.prompt_cost or db_pricing.prompt_cost == "0"):  # type: ignore
            db_pricing.prompt_cost = m.pricing.prompt  # type: ignore
            updated = True

        if m.pricing.completion and (not db_pricing.completion_cost or db_pricing.completion_cost == "0"):  # type: ignore
            db_pricing.completion_cost = m.pricing.completion  # type: ignore
            updated = True

        if m.pricing.request and (not db_pricing.request_cost or db_pricing.request_cost == "0"):  # type: ignore
            db_pricing.request_cost = m.pricing.request  # type: ignore
            updated = True

        if m.pricing.image and (not db_pricing.image_cost or db_pricing.image_cost == "0"):  # type: ignore
            db_pricing.image_cost = m.pricing.image  # type: ignore
            updated = True

        if m.pricing.web_search and (not db_pricing.web_search_cost or db_pricing.web_search_cost == "0"):  # type: ignore
            db_pricing.web_search_cost = m.pricing.web_search  # type: ignore
            updated = True

        if m.pricing.internal_reasoning and (
            not db_pricing.internal_reasoning_cost
            or db_pricing.internal_reasoning_cost == "0"
        ):  # type: ignore
            db_pricing.internal_reasoning_cost = m.pricing.internal_reasoning  # type: ignore
            updated = True

        if updated:
            updated_count += 1

    if updated_count > 0:
        await session.commit()
        logger.info(f"✓ Updated pricing for {updated_count} existing models")

    return updated_count


async def update_existing_endpoint_pricing(
    session: AsyncSession,
    models: list[OpenRouterModelWithEndpoints],
    zdr_lookup: dict[tuple[str, str, str], ZDREndpoint],
) -> int:
    """Update existing endpoint pricing with new data from OpenRouter and ZDR"""
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
            # Get endpoint ID
            result = await session.execute(
                select(ModelEndpoint.id).where(
                    ModelEndpoint.model_id == model_id,
                    ModelEndpoint.name == ep.name,
                    ModelEndpoint.provider_name == ep.provider_name,
                    ModelEndpoint.tag == ep.tag,
                )
            )
            endpoint_id_row = result.scalar_one_or_none()

            if endpoint_id_row is None:
                continue

            endpoint_id = endpoint_id_row

            # Check if pricing exists
            result = await session.execute(
                select(ModelEndpointPricing).where(
                    ModelEndpointPricing.endpoint_id == endpoint_id
                )
            )
            db_pricing = result.scalar_one_or_none()

            if db_pricing is None:
                continue  # Skip if pricing doesn't exist

            # Check if this endpoint has ZDR pricing (preferred)
            zdr_key = (ep.provider_name, ep.model_name, ep.tag)
            zdr_endpoint = zdr_lookup.get(zdr_key)

            updated = False

            if zdr_endpoint:
                # Use ZDR pricing (preferred)
                if zdr_endpoint.pricing.prompt_cost and (not db_pricing.prompt_cost or db_pricing.prompt_cost == "0"):  # type: ignore
                    db_pricing.prompt_cost = zdr_endpoint.pricing.prompt_cost  # type: ignore
                    updated = True

                if zdr_endpoint.pricing.completion_cost and (
                    not db_pricing.completion_cost or db_pricing.completion_cost == "0"
                ):  # type: ignore
                    db_pricing.completion_cost = zdr_endpoint.pricing.completion_cost  # type: ignore
                    updated = True

                if zdr_endpoint.pricing.request_cost and (
                    not db_pricing.request_cost or db_pricing.request_cost == "0"
                ):  # type: ignore
                    db_pricing.request_cost = zdr_endpoint.pricing.request_cost  # type: ignore
                    updated = True

                if zdr_endpoint.pricing.image_cost and (not db_pricing.image_cost or db_pricing.image_cost == "0"):  # type: ignore
                    db_pricing.image_cost = zdr_endpoint.pricing.image_cost  # type: ignore
                    updated = True

                # New ZDR fields
                if zdr_endpoint.pricing.image_output_cost and (
                    not db_pricing.image_output_cost
                    or db_pricing.image_output_cost == "0"
                ):  # type: ignore
                    db_pricing.image_output_cost = zdr_endpoint.pricing.image_output_cost  # type: ignore
                    updated = True

                if zdr_endpoint.pricing.audio_cost and (not db_pricing.audio_cost or db_pricing.audio_cost == "0"):  # type: ignore
                    db_pricing.audio_cost = zdr_endpoint.pricing.audio_cost  # type: ignore
                    updated = True

                if zdr_endpoint.pricing.input_audio_cache_cost and (
                    not db_pricing.input_audio_cache_cost
                    or db_pricing.input_audio_cache_cost == "0"
                ):  # type: ignore
                    db_pricing.input_audio_cache_cost = zdr_endpoint.pricing.input_audio_cache_cost  # type: ignore
                    updated = True

                if zdr_endpoint.pricing.input_cache_read_cost and (
                    not db_pricing.input_cache_read_cost
                    or db_pricing.input_cache_read_cost == "0"
                ):  # type: ignore
                    db_pricing.input_cache_read_cost = zdr_endpoint.pricing.input_cache_read_cost  # type: ignore
                    updated = True

                if zdr_endpoint.pricing.input_cache_write_cost and (
                    not db_pricing.input_cache_write_cost
                    or db_pricing.input_cache_write_cost == "0"
                ):  # type: ignore
                    db_pricing.input_cache_write_cost = zdr_endpoint.pricing.input_cache_write_cost  # type: ignore
                    updated = True

                if zdr_endpoint.pricing.discount and (not db_pricing.discount or db_pricing.discount == "0"):  # type: ignore
                    db_pricing.discount = zdr_endpoint.pricing.discount  # type: ignore
                    updated = True
            else:
                # Use regular endpoint pricing
                if ep.pricing.get("prompt_cost") and (not db_pricing.prompt_cost or db_pricing.prompt_cost == "0"):  # type: ignore
                    db_pricing.prompt_cost = str(ep.pricing["prompt_cost"])  # type: ignore
                    updated = True

                if ep.pricing.get("completion_cost") and (
                    not db_pricing.completion_cost or db_pricing.completion_cost == "0"
                ):  # type: ignore
                    db_pricing.completion_cost = str(ep.pricing["completion_cost"])  # type: ignore
                    updated = True

                if ep.pricing.get("request_cost") and (not db_pricing.request_cost or db_pricing.request_cost == "0"):  # type: ignore
                    db_pricing.request_cost = str(ep.pricing["request_cost"])  # type: ignore
                    updated = True

                if ep.pricing.get("image_cost") and (not db_pricing.image_cost or db_pricing.image_cost == "0"):  # type: ignore
                    db_pricing.image_cost = str(ep.pricing["image_cost"])  # type: ignore
                    updated = True

            if updated:
                updated_count += 1

    if updated_count > 0:
        await session.commit()
        logger.info(f"✓ Updated pricing for {updated_count} existing endpoints")

    return updated_count
