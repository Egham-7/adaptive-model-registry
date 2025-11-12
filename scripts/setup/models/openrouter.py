"""
OpenRouter API models and parsing utilities.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from ..utils.validation import is_valid_default_parameter, is_valid_supported_parameter

logger = logging.getLogger(__name__)


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

    @field_validator("supported_parameters")
    @classmethod
    def validate_supported_parameters(cls, v: list[str]) -> list[str]:
        """Validate that all supported parameters are valid"""
        invalid_params = [
            param for param in v if not is_valid_supported_parameter(param)
        ]
        if invalid_params:
            logger.warning(f"Found invalid supported parameters: {invalid_params}")
            # Filter out invalid parameters instead of failing
            v = [param for param in v if is_valid_supported_parameter(param)]
        return v

    @field_validator("default_parameters")
    @classmethod
    def validate_default_parameters(
        cls, v: Optional[dict[str, Any]]
    ) -> Optional[dict[str, Any]]:
        """Validate that default parameters only contain valid keys"""
        if v is None:
            return v

        invalid_keys = [key for key in v.keys() if not is_valid_default_parameter(key)]
        if invalid_keys:
            logger.warning(f"Found invalid default parameter keys: {invalid_keys}")
            # Remove invalid keys instead of failing
            v = {k: v[k] for k in v.keys() if is_valid_default_parameter(k)}
        return v


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

    @field_validator("supported_parameters")
    @classmethod
    def validate_supported_parameters(cls, v: list[str]) -> list[str]:
        """Validate that all supported parameters are valid"""
        invalid_params = [
            param for param in v if not is_valid_supported_parameter(param)
        ]
        if invalid_params:
            logger.warning(
                f"Found invalid supported parameters in endpoint: {invalid_params}"
            )
            # Filter out invalid parameters instead of failing
            v = [param for param in v if is_valid_supported_parameter(param)]
        return v


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

    @field_validator("supported_parameters")
    @classmethod
    def validate_supported_parameters(cls, v: list[str]) -> list[str]:
        """Validate that all supported parameters are valid"""
        invalid_params = [
            param for param in v if not is_valid_supported_parameter(param)
        ]
        if invalid_params:
            logger.warning(
                f"Found invalid supported parameters in {cls.__name__}: {invalid_params}"
            )
            # Filter out invalid parameters instead of failing
            v = [param for param in v if is_valid_supported_parameter(param)]
        return v

    @field_validator("default_parameters")
    @classmethod
    def validate_default_parameters(
        cls, v: Optional[dict[str, Any]]
    ) -> Optional[dict[str, Any]]:
        """Validate that default parameters only contain valid keys"""
        if v is None:
            return v

        invalid_keys = [key for key in v.keys() if not is_valid_default_parameter(key)]
        if invalid_keys:
            logger.warning(
                f"Found invalid default parameter keys in {cls.__name__}: {invalid_keys}"
            )
            # Remove invalid keys instead of failing
            v = {k: v[k] for k in v.keys() if is_valid_default_parameter(k)}
        return v


def parse_openrouter_model(raw_model: dict[str, Any]) -> Optional[OpenRouterModel]:
    """Parse raw model dict into OpenRouterModel, return None if invalid"""
    try:
        return OpenRouterModel(**raw_model)
    except Exception as e:
        logger.warning(f"Failed to parse model {raw_model.get('id')}: {e}")
        return None
