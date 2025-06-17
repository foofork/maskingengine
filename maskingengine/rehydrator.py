"""Rehydration module for restoring original PII from masked content."""

import json
import re
from typing import Dict, Union, Any, Optional, List, Tuple
from pathlib import Path


class Rehydrator:
    """Restores original PII values from masked content using mask maps."""
    
    def __init__(self):
        """Initialize rehydrator."""
        self.placeholder_pattern = re.compile(r'<<([A-Z0-9_]+)_([A-F0-9]{6})_(\d+)>>')
    
    def rehydrate(self, masked_content: Union[str, Dict, Any], mask_map: Dict[str, str]) -> Union[str, Dict, Any]:
        """
        Restore original PII values in masked content.
        
        Args:
            masked_content: Content with PII placeholders
            mask_map: Mapping of placeholders to original values
            
        Returns:
            Content with original PII values restored
            
        Raises:
            ValueError: If placeholder format is invalid or mapping incomplete
        """
        if not mask_map:
            return masked_content
        
        # Handle different content types
        if isinstance(masked_content, dict):
            return self._rehydrate_json(masked_content, mask_map)
        elif isinstance(masked_content, str):
            return self._rehydrate_text(masked_content, mask_map)
        else:
            # Convert to string and rehydrate
            return self._rehydrate_text(str(masked_content), mask_map)
    
    def _rehydrate_text(self, text: str, mask_map: Dict[str, str]) -> str:
        """Rehydrate text content."""
        result = text
        
        # Find all placeholders in the text
        placeholders = self.placeholder_pattern.findall(text)
        
        for pii_type, hash_value, index in placeholders:
            placeholder = f"<<{pii_type}_{hash_value}_{index}>>"
            
            if placeholder in mask_map:
                original_value = mask_map[placeholder]
                result = result.replace(placeholder, original_value)
            else:
                # Optionally raise an error for missing mappings
                print(f"Warning: No mapping found for placeholder {placeholder}")
        
        return result
    
    def _rehydrate_json(self, data: Dict, mask_map: Dict[str, str]) -> Dict:
        """Rehydrate JSON/dict content recursively."""
        if isinstance(data, dict):
            return {key: self._rehydrate_json(value, mask_map) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._rehydrate_json(item, mask_map) for item in data]
        elif isinstance(data, str):
            return self._rehydrate_text(data, mask_map)
        else:
            return data
    
    def validate_mask_map(self, mask_map: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        Validate mask map format and placeholder consistency.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        if not isinstance(mask_map, dict):
            return False, ["Mask map must be a dictionary"]
        
        for placeholder, original_value in mask_map.items():
            # Check placeholder format
            if not self.placeholder_pattern.match(placeholder):
                issues.append(f"Invalid placeholder format: {placeholder}")
            
            # Check that original value is not empty
            if not original_value or not isinstance(original_value, str):
                issues.append(f"Invalid original value for {placeholder}: {original_value}")
        
        return len(issues) == 0, issues
    
    def extract_placeholders(self, content: Union[str, Dict]) -> List[str]:
        """
        Extract all placeholders from content.
        
        Args:
            content: Content to search for placeholders
            
        Returns:
            List of unique placeholders found
        """
        placeholders = set()
        
        if isinstance(content, dict):
            content_str = json.dumps(content)
        else:
            content_str = str(content)
        
        matches = self.placeholder_pattern.findall(content_str)
        for pii_type, hash_value, index in matches:
            placeholder = f"<<{pii_type}_{hash_value}_{index}>>"
            placeholders.add(placeholder)
        
        return list(placeholders)
    
    def check_rehydration_compatibility(self, masked_content: Union[str, Dict], mask_map: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        Check if masked content can be fully rehydrated with the given mask map.
        
        Returns:
            Tuple of (can_rehydrate, list_of_issues)
        """
        issues = []
        
        # Validate mask map format
        is_valid, validation_issues = self.validate_mask_map(mask_map)
        if not is_valid:
            issues.extend(validation_issues)
        
        # Find placeholders in content
        content_placeholders = self.extract_placeholders(masked_content)
        
        # Check if all placeholders have mappings
        missing_mappings = []
        for placeholder in content_placeholders:
            if placeholder not in mask_map:
                missing_mappings.append(placeholder)
        
        if missing_mappings:
            issues.append(f"Missing mappings for placeholders: {missing_mappings}")
        
        # Check for unused mappings (not necessarily an error, but worth noting)
        unused_mappings = []
        for placeholder in mask_map.keys():
            if placeholder not in content_placeholders:
                unused_mappings.append(placeholder)
        
        if unused_mappings:
            issues.append(f"Unused mappings (not found in content): {unused_mappings}")
        
        return len(issues) == 0, issues


class RehydrationStorage:
    """Handles storage and retrieval of mask maps for later rehydration."""
    
    def __init__(self, storage_dir: str = "rehydration_storage"):
        """Initialize storage system."""
        self.storage_dir = Path(storage_dir)
        try:
            self.storage_dir.mkdir(exist_ok=True)
        except (PermissionError, OSError) as e:
            print(f"Warning: Cannot create storage directory {storage_dir}: {e}")
            # Fall back to temp directory
            import tempfile
            self.storage_dir = Path(tempfile.mkdtemp(prefix="maskingengine_"))
    
    def store_mask_map(self, session_id: str, mask_map: Dict[str, str]) -> str:
        """
        Store mask map with a session ID.
        
        Args:
            session_id: Unique identifier for this masking session
            mask_map: Mapping of placeholders to original values
            
        Returns:
            File path where mask map was stored
            
        Raises:
            IOError: If storage fails
        """
        file_path = self.storage_dir / f"{session_id}.json"
        
        try:
            with open(file_path, 'w') as f:
                json.dump(mask_map, f, indent=2)
        except (IOError, PermissionError, OSError) as e:
            raise IOError(f"Failed to store mask map for session '{session_id}': {e}")
        
        return str(file_path)
    
    def load_mask_map(self, session_id: str) -> Optional[Dict[str, str]]:
        """
        Load mask map by session ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Mask map dictionary or None if not found
        """
        file_path = self.storage_dir / f"{session_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def delete_mask_map(self, session_id: str) -> bool:
        """
        Delete stored mask map.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully, False if not found
        """
        file_path = self.storage_dir / f"{session_id}.json"
        
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def list_sessions(self) -> List[str]:
        """List all stored session IDs."""
        return [f.stem for f in self.storage_dir.glob("*.json")]
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """
        Clean up old session files.
        
        Args:
            max_age_hours: Maximum age in hours before deletion
        """
        import time
        
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        for file_path in self.storage_dir.glob("*.json"):
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()


class RehydrationPipeline:
    """High-level pipeline for sanitization with rehydration support."""
    
    def __init__(self, sanitizer, storage: Optional[RehydrationStorage] = None):
        """
        Initialize pipeline with sanitizer and optional storage.
        
        Args:
            sanitizer: MaskingEngine Sanitizer instance
            storage: Optional storage system for mask maps
        """
        self.sanitizer = sanitizer
        self.rehydrator = Rehydrator()
        self.storage = storage or RehydrationStorage()
    
    def sanitize_with_session(self, content: Union[str, Dict], session_id: str, 
                            format: Optional[str] = None) -> Tuple[Union[str, Dict], str]:
        """
        Sanitize content and store mask map for later rehydration.
        
        Args:
            content: Content to sanitize
            session_id: Unique session identifier
            format: Content format (optional)
            
        Returns:
            Tuple of (masked_content, storage_path)
        """
        # Sanitize content
        masked_content, mask_map = self.sanitizer.sanitize(content, format)
        
        # Store mask map
        storage_path = self.storage.store_mask_map(session_id, mask_map)
        
        return masked_content, storage_path
    
    def rehydrate_with_session(self, masked_content: Union[str, Dict], session_id: str) -> Optional[Union[str, Dict]]:
        """
        Rehydrate content using stored mask map.
        
        Args:
            masked_content: Content with placeholders
            session_id: Session identifier
            
        Returns:
            Rehydrated content or None if session not found
        """
        # Load mask map
        mask_map = self.storage.load_mask_map(session_id)
        if mask_map is None:
            return None
        
        # Rehydrate content
        return self.rehydrator.rehydrate(masked_content, mask_map)
    
    def complete_session(self, session_id: str) -> bool:
        """
        Complete session and clean up stored mask map.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if cleanup successful
        """
        return self.storage.delete_mask_map(session_id)