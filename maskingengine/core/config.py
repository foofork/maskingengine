"""Configuration module for MaskingEngine."""

from typing import List, Optional
from pydantic import BaseModel, Field, validator


class SanitizerConfig(BaseModel):
    """Configuration for the MaskingEngine sanitizer."""
    
    enable_regex: bool = Field(
        default=True,
        description="Enables detection of structured PII using regex patterns"
    )
    enable_ner: bool = Field(
        default=True,
        description="Enables transformer model for detecting unstructured PII"
    )
    confidence_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score (0.0-1.0) for NER model to flag entity as PII"
    )
    whitelist: List[str] = Field(
        default_factory=list,
        description="List of strings to ignore. Matching is case-insensitive and targets whole words"
    )
    placeholder_prefix: str = Field(
        default="<<",
        description="Opening characters for a placeholder"
    )
    placeholder_suffix: str = Field(
        default=">>",
        description="Closing characters for a placeholder"
    )
    logging_enabled: bool = Field(
        default=False,
        description="If true, enables non-PII operational logging"
    )
    max_input_characters: int = Field(
        default=50000,
        gt=0,
        description="Maximum allowed character length of input text"
    )
    
    @validator("confidence_threshold")
    def validate_confidence_threshold(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")
        return v
    
    @validator("whitelist")
    def normalize_whitelist(cls, v):
        return [item.lower() for item in v]
    
    class Config:
        validate_assignment = True