"""
ZDR (Zero Downtime Routing) endpoint models.
"""


from pydantic import BaseModel, field_validator


class ZDREndpointPricing(BaseModel):
    """ZDR endpoint pricing information"""

    prompt_cost: str = "0"
    completion_cost: str = "0"
    request_cost: str = "0"
    image_cost: str = "0"
    image_output_cost: str = "0"
    audio_cost: str = "0"
    input_audio_cache_cost: str = "0"
    input_cache_read_cost: str = "0"
    input_cache_write_cost: str = "0"
    discount: str = "0"

    @field_validator("discount", mode="before")
    @classmethod
    def validate_discount(cls, v: str | int | float) -> str:
        """Convert discount to string if it's a number"""
        if isinstance(v, (int, float)):
            return str(v)
        return v


class ZDREndpoint(BaseModel):
    """ZDR endpoint information from /api/v1/endpoints/zdr"""

    provider_name: str
    model_name: str
    tag: str
    pricing: ZDREndpointPricing
