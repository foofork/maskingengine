"""Simplified masker module for <<TYPE_HASH>> replacement."""

from typing import List, Tuple
from .config import Config


class Masker:
    """Simple masker that creates configurable placeholders."""
    
    def __init__(self, type_hashes: dict = None, config: Config = None):
        self.type_hashes = type_hashes or Config.TYPE_HASHES
        self.type_counters = {}
        self.config = config or Config()
    
    def mask(self, text: str, detections: List[Tuple[str, str, int, int]], mask_map: dict = None) -> str:
        """Apply masks to text using deterministic placeholders."""
        if not detections:
            return text
        
        # Sort detections in reverse order (right to left)
        sorted_detections = sorted(detections, key=lambda d: d[2], reverse=True)
        
        # Apply masks from end to beginning to preserve positions
        result = text
        for detection in sorted_detections:
            pii_type, pii_text, start, end = detection
            placeholder = self._get_placeholder(pii_type)
            
            # Store original value in mask map if provided
            if mask_map is not None:
                mask_map[placeholder] = pii_text
            
            result = result[:start] + placeholder + result[end:]
        
        return result
    
    def _get_placeholder(self, pii_type: str) -> str:
        """Generate deterministic placeholder for PII type with index."""
        # Normalize type mapping for NER entities
        type_map = {
            'PERSON': 'PERSON',
            'ORG': 'ORGANIZATION',
            'ORGANIZATION': 'ORGANIZATION', 
            'GPE': 'LOCATION',
            'LOCATION': 'LOCATION'
        }
        
        normalized_type = type_map.get(pii_type, pii_type)
        hash_value = self.type_hashes.get(normalized_type, 'XXXXXX')
        
        # Get and increment counter for this type
        if normalized_type not in self.type_counters:
            self.type_counters[normalized_type] = 0
        self.type_counters[normalized_type] += 1
        
        # Use configured placeholder format
        if self.config.placeholder_prefix.startswith('<<'):
            # Default format: <<TYPE_HASH_INDEX>>
            return f"<<{normalized_type}_{hash_value}_{self.type_counters[normalized_type]}>>"
        else:
            # Custom format: [PREFIX]TYPE_HASH_INDEX[/PREFIX]
            prefix = self.config.placeholder_prefix
            return f"{prefix}{normalized_type}_{hash_value}_{self.type_counters[normalized_type]}{prefix}"