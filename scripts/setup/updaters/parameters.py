"""
Update functions for parameter tables.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import LLMModel, ModelDefaultParameters, ModelSupportedParameter
from ..models.openrouter import OpenRouterModelWithEndpoints
from ..utils.validation import (
    DefaultParametersValues,
    SupportedParameter,
    is_valid_default_parameter,
    is_valid_supported_parameter,
)

logger = logging.getLogger(__name__)


async def update_existing_supported_parameters(
    session: AsyncSession, models: list[OpenRouterModelWithEndpoints]
) -> int:
    """Update existing supported parameters with new data from OpenRouter"""
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

        # Get existing supported parameters
        result = await session.execute(
            select(ModelSupportedParameter.parameter_name).where(
                ModelSupportedParameter.model_id == model_id
            )
        )
        existing_params = {row[0] for row in result.all()}

        # Add missing parameters
        for param in m.supported_parameters:
            if param not in existing_params:
                # Validate parameter name
                if not is_valid_supported_parameter(param):
                    continue

                new_param = ModelSupportedParameter(
                    model_id=model_id, parameter_name=SupportedParameter(param)
                )
                session.add(new_param)
                updated_count += 1

    if updated_count > 0:
        await session.commit()
        logger.info(f"✓ Added {updated_count} new supported parameters")

    return updated_count


async def update_existing_default_parameters(
    session: AsyncSession, models: list[OpenRouterModelWithEndpoints]
) -> int:
    """Update existing default parameters with new data from OpenRouter"""
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

        # Check if default parameters exist
        result = await session.execute(
            select(ModelDefaultParameters).where(
                ModelDefaultParameters.model_id == model_id
            )
        )
        db_defaults = result.scalar_one_or_none()

        if db_defaults is None:
            continue  # Skip if default parameters don't exist

        # Merge default parameters if they exist
        if m.default_parameters:
            # Filter to only valid default parameters
            valid_defaults = {
                k: v
                for k, v in m.default_parameters.items()
                if is_valid_default_parameter(k)
            }

            if valid_defaults:
                # Merge with existing parameters
                existing_params = db_defaults.parameters or {}  # type: ignore
                merged_params = {**existing_params, **valid_defaults}  # type: ignore

                # Create new DefaultParametersValues
                new_defaults = DefaultParametersValues(**merged_params)
                db_defaults.parameters = new_defaults.model_dump(exclude_none=True)  # type: ignore
                updated_count += 1

    if updated_count > 0:
        await session.commit()
        logger.info(f"✓ Updated default parameters for {updated_count} existing models")

    return updated_count
