"""
Update functions for architecture tables.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import LLMModel, ModelArchitecture, ModelArchitectureModality
from ..models.openrouter import OpenRouterModelWithEndpoints

logger = logging.getLogger(__name__)


async def update_existing_model_architecture(
    session: AsyncSession, models: list[OpenRouterModelWithEndpoints]
) -> int:
    """Update existing model architecture with new data from OpenRouter"""
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

        # Check if architecture exists
        result = await session.execute(
            select(ModelArchitecture).where(ModelArchitecture.model_id == model_id)
        )
        db_arch = result.scalar_one_or_none()

        if db_arch is None:
            continue  # Skip if architecture doesn't exist

        # Update architecture fields if they have meaningful values
        updated = False

        if m.architecture.modality and (not db_arch.modality or db_arch.modality == ""):  # type: ignore
            db_arch.modality = m.architecture.modality  # type: ignore
            updated = True

        if m.architecture.tokenizer and (not db_arch.tokenizer or db_arch.tokenizer == ""):  # type: ignore
            db_arch.tokenizer = m.architecture.tokenizer  # type: ignore
            updated = True

        if m.architecture.instruct_type and (not db_arch.instruct_type or db_arch.instruct_type == ""):  # type: ignore
            db_arch.instruct_type = m.architecture.instruct_type  # type: ignore
            updated = True

        if updated:
            updated_count += 1

    if updated_count > 0:
        await session.commit()
        logger.info(f"✓ Updated architecture for {updated_count} existing models")

    return updated_count


async def update_existing_architecture_modalities(
    session: AsyncSession, models: list[OpenRouterModelWithEndpoints]
) -> int:
    """Update existing architecture modalities with new data from OpenRouter"""
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

        # Get architecture ID
        result = await session.execute(
            select(ModelArchitecture.id).where(ModelArchitecture.model_id == model_id)
        )
        arch_id_row = result.scalar_one_or_none()

        if arch_id_row is None:
            continue

        arch_id = arch_id_row

        # Get existing modalities
        result = await session.execute(
            select(
                ModelArchitectureModality.modality_type,
                ModelArchitectureModality.modality_value,
            ).where(ModelArchitectureModality.architecture_id == arch_id)
        )
        existing_modalities = {(row[0], row[1]) for row in result.all()}

        # Add missing modalities
        for input_modality in m.architecture.input_modalities:
            if ("input", input_modality) not in existing_modalities:
                new_modality = ModelArchitectureModality(
                    architecture_id=arch_id,
                    modality_type="input",
                    modality_value=input_modality,
                )
                session.add(new_modality)
                updated_count += 1

        for output_modality in m.architecture.output_modalities:
            if ("output", output_modality) not in existing_modalities:
                new_modality = ModelArchitectureModality(
                    architecture_id=arch_id,
                    modality_type="output",
                    modality_value=output_modality,
                )
                session.add(new_modality)
                updated_count += 1

    if updated_count > 0:
        await session.commit()
        logger.info(f"✓ Added {updated_count} new architecture modalities")

    return updated_count
