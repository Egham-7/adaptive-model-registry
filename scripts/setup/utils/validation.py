"""
Parameter validation utilities for model registry setup.
"""

import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ============================================================================
# PARAMETER TYPE CONSTANTS (MUST MATCH Go CODE IN internal/models/parameters.go)
# ============================================================================
# These constants must be kept in sync with the Go parameter definitions
# in adaptive-model-registry/internal/models/parameters.go and
# adaptive-proxy/internal/models/parameters.go

# Supported parameter names (all parameters a model can support)
SUPPORTED_PARAMETERS = [
    # Sampling parameters
    "temperature",
    "top_p",
    "top_k",
    "min_p",
    "top_a",
    # Penalty parameters
    "frequency_penalty",
    "presence_penalty",
    "repetition_penalty",
    # Token and output parameters
    "top_logprobs",
    "seed",
    "max_tokens",
    "max_output_tokens",
    "max_completion_tokens",
    # Response format parameters
    "response_format",
    "structured_outputs",
    # Control parameters
    "stop",
    "stop_sequences",
    "tools",
    "tool_choice",
    "parallel_tool_calls",
    # Additional parameters
    "n",
    "candidate_count",
    "store",
    "logprobs",
    "logit_bias",
    "web_search_options",
    # Reasoning parameters
    "include_reasoning",
    "reasoning",
]

# Default parameter names (subset that can have default values)
DEFAULT_PARAMETERS = [
    "temperature",
    "top_p",
    "frequency_penalty",
]


# ============================================================================
# PYTHON EQUIVALENTS OF GO TYPES (for validation)
# ============================================================================


class SupportedParameter(str):
    """Python equivalent of Go SupportedParameter enum"""

    TEMPERATURE = "temperature"
    TOP_P = "top_p"
    TOP_K = "top_k"
    MIN_P = "min_p"
    TOP_A = "top_a"
    FREQUENCY_PENALTY = "frequency_penalty"
    PRESENCE_PENALTY = "presence_penalty"
    REPETITION_PENALTY = "repetition_penalty"
    TOP_LOGPROBS = "top_logprobs"
    SEED = "seed"
    MAX_TOKENS = "max_tokens"
    MAX_OUTPUT_TOKENS = "max_output_tokens"
    MAX_COMPLETION_TOKENS = "max_completion_tokens"
    RESPONSE_FORMAT = "response_format"
    STRUCTURED_OUTPUTS = "structured_outputs"
    STOP = "stop"
    STOP_SEQUENCES = "stop_sequences"
    TOOLS = "tools"
    TOOL_CHOICE = "tool_choice"
    PARALLEL_TOOL_CALLS = "parallel_tool_calls"
    N = "n"
    CANDIDATE_COUNT = "candidate_count"
    STORE = "store"
    LOGPROBS = "logprobs"
    LOGIT_BIAS = "logit_bias"
    WEB_SEARCH_OPTIONS = "web_search_options"
    INCLUDE_REASONING = "include_reasoning"
    REASONING = "reasoning"


class DefaultParametersValues(BaseModel):
    """Python equivalent of Go DefaultParametersValues"""

    temperature: float | None = None
    top_p: float | None = None
    top_k: float | None = None
    min_p: float | None = None
    top_a: float | None = None
    frequency_penalty: float | None = None
    max_tokens: float | None = None
    max_completion_tokens: float | None = None
    top_logprobs: float | None = None
    seed: float | None = None
    n: float | None = None
    stop_sequences: list[str] | None = None
    parallel_tool_calls: bool | None = None
    store: bool | None = None
    logprobs: bool | None = None


def is_valid_supported_parameter(param: str) -> bool:
    """Check if a parameter name is valid for supported parameters"""
    return param in SUPPORTED_PARAMETERS


def is_valid_default_parameter(param: str) -> bool:
    """Check if a parameter name is valid for default parameters"""
    return param in DEFAULT_PARAMETERS


def validate_parameter_constants() -> None:
    """Validate that parameter constants are properly defined"""
    # Ensure no duplicates
    if len(SUPPORTED_PARAMETERS) != len(set(SUPPORTED_PARAMETERS)):
        raise ValueError("SUPPORTED_PARAMETERS contains duplicates")

    if len(DEFAULT_PARAMETERS) != len(set(DEFAULT_PARAMETERS)):
        raise ValueError("DEFAULT_PARAMETERS contains duplicates")

    # Ensure default parameters are a subset of supported parameters
    invalid_defaults = set(DEFAULT_PARAMETERS) - set(SUPPORTED_PARAMETERS)
    if invalid_defaults:
        raise ValueError(
            f"DEFAULT_PARAMETERS contains parameters not in SUPPORTED_PARAMETERS: {invalid_defaults}"
        )

    logger.debug(
        f"✓ Parameter constants validated: {len(SUPPORTED_PARAMETERS)} supported, {len(DEFAULT_PARAMETERS)} default"
    )
