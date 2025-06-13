"""Deterministic masking and rehydration system."""

import hashlib
from typing import Dict, List, Tuple, Any


class MaskingEngine:
    """Handles deterministic masking and rehydration of PII."""
    
    def __init__(self, prefix: str = "<<", suffix: str = ">>"):
        self.prefix = prefix
        self.suffix = suffix
    
    def mask_text(self, text: str, detections: List[Dict[str, Any]]) -> Tuple[str, Dict[str, str]]:
        """
        Apply masking to detected PII in text.
        
        Args:
            text: Original text
            detections: List of PII detections
            
        Returns:
            Tuple of (masked_text, rehydration_map)
        """
        if not detections:
            return text, {}
        
        # Sort detections by position (reverse order for replacement)
        sorted_detections = sorted(detections, key=lambda x: x["start"], reverse=True)
        
        masked_text = text
        rehydration_map = {}
        
        for detection in sorted_detections:
            # Generate deterministic placeholder
            placeholder = self._generate_placeholder(
                detection["type"],
                detection["text"]
            )
            
            # Replace in text
            start = detection["start"]
            end = detection["end"]
            masked_text = masked_text[:start] + placeholder + masked_text[end:]
            
            # Add to rehydration map
            rehydration_map[placeholder] = detection["text"]
        
        return masked_text, rehydration_map
    
    def _generate_placeholder(self, entity_type: str, text: str) -> str:
        """
        Generate a deterministic placeholder for a PII value.
        
        Args:
            entity_type: Type of entity (EMAIL, PHONE, etc.)
            text: The actual PII text
            
        Returns:
            Deterministic placeholder string
        """
        # Create a hash of the content for deterministic generation
        content_hash = hashlib.sha256(text.encode()).hexdigest()[:8]
        
        # Format: <<TYPE_HASH>>
        placeholder = f"{self.prefix}{entity_type}_{content_hash}{self.suffix}"
        
        return placeholder
    
    def rehydrate_text(self, masked_text: str, rehydration_map: Dict[str, str]) -> str:
        """
        Restore original PII values from masked text.
        
        Args:
            masked_text: Text with placeholders
            rehydration_map: Mapping of placeholders to original values
            
        Returns:
            Original text with PII restored
        """
        if not rehydration_map:
            return masked_text
        
        rehydrated_text = masked_text
        
        # Sort by placeholder length (longest first) to avoid partial replacements
        sorted_placeholders = sorted(
            rehydration_map.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        for placeholder, original_value in sorted_placeholders:
            rehydrated_text = rehydrated_text.replace(placeholder, original_value)
        
        return rehydrated_text
    
    def validate_rehydration_map(self, rehydration_map: Dict[str, str]) -> bool:
        """
        Validate that a rehydration map is well-formed.
        
        Args:
            rehydration_map: Map to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(rehydration_map, dict):
            return False
        
        for placeholder, value in rehydration_map.items():
            # Check placeholder format
            if not (placeholder.startswith(self.prefix) and 
                    placeholder.endswith(self.suffix)):
                return False
            
            # Check that value is a string
            if not isinstance(value, str):
                return False
        
        return True
    
    def merge_rehydration_maps(self, *maps: Dict[str, str]) -> Dict[str, str]:
        """
        Merge multiple rehydration maps, handling conflicts.
        
        Args:
            *maps: Variable number of rehydration maps
            
        Returns:
            Merged rehydration map
        """
        merged = {}
        
        for map_dict in maps:
            for placeholder, value in map_dict.items():
                if placeholder in merged and merged[placeholder] != value:
                    # Log warning about conflict
                    # In production, this might need more sophisticated handling
                    pass
                merged[placeholder] = value
        
        return merged