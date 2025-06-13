"""Main sanitizer interface for the MaskingEngine library."""

import logging
from typing import Dict, Tuple, Optional, Union, Any

from .config import SanitizerConfig
from .pipeline import SanitizationPipeline
from .masking import MaskingEngine
from .parsers import BaseParser


def sanitize(
    text: str,
    config: Optional[Union[Dict[str, Any], SanitizerConfig]] = None,
    content_type: str = "text"
) -> Tuple[str, Dict[str, str]]:
    """
    Sanitize PII from text.
    
    Args:
        text: Input text to sanitize
        config: Optional configuration dict or SanitizerConfig object
        content_type: Type of content ("text", "json", or "html")
        
    Returns:
        Tuple of (masked_text, rehydration_map)
        
    Raises:
        ValueError: If input validation fails
        RuntimeError: If sanitization fails
    """
    # Handle configuration
    if config is None:
        sanitizer_config = SanitizerConfig()
    elif isinstance(config, dict):
        sanitizer_config = SanitizerConfig(**config)
    else:
        sanitizer_config = config
    
    # Set up logging if enabled
    if sanitizer_config.logging_enabled:
        logging.basicConfig(level=logging.INFO)
    
    try:
        # Create pipeline
        pipeline = SanitizationPipeline(sanitizer_config)
        
        # Process through pipeline
        processed_text, detections, parser_metadata = pipeline.process(text, content_type)
        
        # Deduplicate detections
        unique_detections = pipeline.deduplicate_detections(detections)
        
        # Create masking engine
        masker = MaskingEngine(
            prefix=sanitizer_config.placeholder_prefix,
            suffix=sanitizer_config.placeholder_suffix
        )
        
        # Apply masking
        masked_text, rehydration_map = masker.mask_text(processed_text, unique_detections)
        
        # Reconstruct format if needed
        if content_type != "text" and parser_metadata:
            parser = pipeline.parsers[content_type]
            masked_text = parser.reconstruct(masked_text, parser_metadata)
        
        return masked_text, rehydration_map
        
    except ValueError as e:
        # Re-raise validation errors
        raise
    except Exception as e:
        # Wrap other errors
        raise RuntimeError(f"Sanitization failed: {e}")


def rehydrate(
    masked_text: str,
    rehydration_map: Dict[str, str],
    content_type: str = "text"
) -> str:
    """
    Restore original PII values from masked text.
    
    Args:
        masked_text: Text containing placeholders
        rehydration_map: Mapping of placeholders to original values
        content_type: Type of content (for future format support)
        
    Returns:
        Original text with PII restored
        
    Raises:
        ValueError: If rehydration map is invalid
    """
    # Create masking engine with default settings
    # In practice, these should match the original sanitization settings
    masker = MaskingEngine()
    
    # Validate rehydration map
    if not masker.validate_rehydration_map(rehydration_map):
        raise ValueError("Invalid rehydration map format")
    
    # Perform rehydration
    return masker.rehydrate_text(masked_text, rehydration_map)