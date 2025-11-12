"""
Bulk insertion logic for new models.
"""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import (
    LLMModel,
    ModelArchitecture,
    ModelArchitectureModality,
    ModelDefaultParameters,
    ModelEndpoint,
    ModelEndpointPricing,
    ModelPricing,
    ModelSupportedParameter,
    ModelTopProvider,
)
from ..models.openrouter import OpenRouterModelWithEndpoints
from ..models.zdr import ZDREndpoint

logger = logging.getLogger(__name__)


async def get_existing_models_from_db(session: AsyncSession) -> set[tuple[str, str]]:
    """Get existing (author, model_name) tuples from database"""
    result = await session.execute(select(LLMModel.author, LLMModel.model_name))
    return {(row[0], row[1]) for row in result.all()}


async def bulk_insert_models(
    session: AsyncSession,
    models: list[OpenRouterModelWithEndpoints],
    zdr_lookup: dict[tuple[str, str, str], ZDREndpoint]
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
                    # Check if this endpoint is ZDR-enabled
                    zdr_key = (ep.provider_name, ep.model_name, ep.tag)
                    is_zdr = "true" if zdr_key in zdr_lookup else "false"

                    endpoint = ModelEndpoint(
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
                        is_zdr=is_zdr,
                    )
                    session.add(endpoint)
                    await session.flush()  # Get endpoint ID

                    # 9. Insert endpoint pricing (only for new endpoints)
                    # Use ZDR pricing if available, otherwise use endpoint pricing
                    zdr_endpoint = zdr_lookup.get(zdr_key)
                    if zdr_endpoint:
                        endpoint_pricing = ModelEndpointPricing(
                            endpoint_id=endpoint.id,
                            prompt_cost=zdr_endpoint.pricing.prompt_cost,
                            completion_cost=zdr_endpoint.pricing.completion_cost,
                            request_cost=zdr_endpoint.pricing.request_cost,
                            image_cost=zdr_endpoint.pricing.image_cost,
                            image_output_cost=zdr_endpoint.pricing.image_output_cost,
                            audio_cost=zdr_endpoint.pricing.audio_cost,
                            input_audio_cache_cost=zdr_endpoint.pricing.input_audio_cache_cost,
                            input_cache_read_cost=zdr_endpoint.pricing.input_cache_read_cost,
                            input_cache_write_cost=zdr_endpoint.pricing.input_cache_write_cost,
                            discount=zdr_endpoint.pricing.discount,
                        )
                    else:
                        endpoint_pricing = ModelEndpointPricing(
                            endpoint_id=endpoint.id,
                            prompt_cost=ep.pricing.get("prompt", "0"),
                            completion_cost=ep.pricing.get("completion", "0"),
                            request_cost=ep.pricing.get("request", "0"),
                            image_cost=ep.pricing.get("image", "0"),
                            image_output_cost="0",
                            audio_cost="0",
                            input_audio_cache_cost="0",
                            input_cache_read_cost="0",
                            input_cache_write_cost="0",
                            discount="0",
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