"""
Export utilities for saving models to various formats.
"""

import logging
from pathlib import Path

import polars as pl

from ..models.openrouter import OpenRouterModelWithEndpoints

logger = logging.getLogger(__name__)


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
