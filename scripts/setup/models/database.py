"""
SQLAlchemy database models for the model registry.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase


# SQLAlchemy Base
class Base(DeclarativeBase):
    pass


# ============================================================================
# NORMALIZED SQLALCHEMY MODELS
# ============================================================================


class LLMModel(Base):
    """Core model table with basic metadata"""

    __tablename__ = "llm_models"
    __table_args__ = (UniqueConstraint("author", "model_name", name="uq_author_model"),)

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Author and model name form the composite unique identifier
    author = Column(String(50), nullable=False, index=True)
    model_name = Column(String(255), nullable=False, index=True)

    # Basic metadata
    display_name = Column(String(255))
    description = Column(Text)
    context_length = Column(Integer)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    last_updated = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ModelPricing(Base):
    """Model pricing information (one-to-one with LLMModel)"""

    __tablename__ = "model_pricing"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )

    # Pricing in USD per token (using NUMERIC for precision)
    prompt_cost = Column(String(50), nullable=False)  # Keep as string for precision
    completion_cost = Column(String(50), nullable=False)
    request_cost = Column(String(50), nullable=False, default="0")
    image_cost = Column(String(50), nullable=False, default="0")
    web_search_cost = Column(String(50), nullable=False, default="0")
    internal_reasoning_cost = Column(String(50), nullable=False, default="0")


class ModelArchitecture(Base):
    """Model architecture metadata (one-to-one with LLMModel)"""

    __tablename__ = "model_architecture"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )

    modality = Column(String(50), nullable=False)
    tokenizer = Column(String(100), nullable=False)
    instruct_type = Column(String(50))


class ModelArchitectureModality(Base):
    """Input/output modalities for model architecture (many-to-one with ModelArchitecture)"""

    __tablename__ = "model_architecture_modalities"
    __table_args__ = (
        UniqueConstraint(
            "architecture_id",
            "modality_type",
            "modality_value",
            name="uq_arch_modality",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    architecture_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    # 'input' or 'output'
    modality_type = Column(String(10), nullable=False)
    modality_value = Column(String(50), nullable=False)


class ModelTopProvider(Base):
    """Top provider metadata (one-to-one with LLMModel)"""

    __tablename__ = "model_top_provider"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )

    context_length = Column(Integer)
    max_completion_tokens = Column(Integer)
    is_moderated = Column(String(10), nullable=False, default="false")


class ModelEndpoint(Base):
    """Model endpoint information (one-to-many with LLMModel)"""

    __tablename__ = "model_endpoints"
    __table_args__ = (
        UniqueConstraint(
            "model_id", "name", "provider_name", "tag", name="uq_model_endpoint"
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    name = Column(String(255), nullable=False)
    endpoint_model_name = Column(String(255), nullable=False)
    context_length = Column(Integer, nullable=False)
    provider_name = Column(String(100), nullable=False, index=True)
    tag = Column(String(100), nullable=False)
    quantization = Column(String(50))
    max_completion_tokens = Column(Integer)
    max_prompt_tokens = Column(Integer)
    status = Column(Integer, nullable=False)
    uptime_last_30m = Column(String(50))
    supports_implicit_caching = Column(String(10), nullable=False, default="false")
    is_zdr = Column(String(10), nullable=False, default="false")


class ModelEndpointPricing(Base):
    """Endpoint-specific pricing (one-to-one with ModelEndpoint)"""

    __tablename__ = "model_endpoint_pricing"

    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint_id = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )

    prompt_cost = Column(String(50), nullable=False, default="0")
    completion_cost = Column(String(50), nullable=False, default="0")
    request_cost = Column(String(50), nullable=False, default="0")
    image_cost = Column(String(50), nullable=False, default="0")
    image_output_cost = Column(String(50), nullable=False, default="0")
    audio_cost = Column(String(50), nullable=False, default="0")
    input_audio_cache_cost = Column(String(50), nullable=False, default="0")
    input_cache_read_cost = Column(String(50), nullable=False, default="0")
    input_cache_write_cost = Column(String(50), nullable=False, default="0")
    discount = Column(String(50), nullable=False, default="0")


class ModelSupportedParameter(Base):
    """Supported parameters for model (many-to-many with LLMModel)"""

    __tablename__ = "model_supported_parameters"
    __table_args__ = (
        UniqueConstraint("model_id", "parameter_name", name="uq_model_parameter"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    parameter_name = Column(String(100), nullable=False)


class ModelDefaultParameters(Base):
    """Default parameters for model (one-to-one with LLMModel, stored as JSON for flexibility)"""

    __tablename__ = "model_default_parameters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )

    parameters = Column(JSON)


class SyncMetadata(Base):
    """Tracks synchronization metadata to avoid unnecessary API calls"""

    __tablename__ = "sync_metadata"

    id = Column(Integer, primary_key=True)
    sync_type = Column(
        String, nullable=False, index=True
    )  # "openrouter_models", "zdr_endpoints"
    last_sync_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    models_count = Column(Integer)
    zdr_endpoints_count = Column(Integer)

    __table_args__ = (UniqueConstraint("sync_type"),)
