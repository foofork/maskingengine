"""Simplified masker module for <<TYPE_HASH>> replacement."""

from typing import List, Tuple
from .config import Config


class Masker:
    """Simple masker that creates <<TYPE_HASH>> placeholders."""
    
    def __init__(self, type_hashes: dict = None):
        self.type_hashes = type_hashes or Config.TYPE_HASHES
    
    def mask(self, text: str, detections: List[Tuple[str, str, int, int]]) -> str:
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
            result = result[:start] + placeholder + result[end:]
        
        return result
    
    def _get_placeholder(self, pii_type: str) -> str:
        """Generate deterministic placeholder for PII type."""
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
        return f"<<{normalized_type}_{hash_value}>>"