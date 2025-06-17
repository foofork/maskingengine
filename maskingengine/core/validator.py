"""Configuration validation module."""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import yaml

try:
    import jsonschema
except ImportError:
    jsonschema = None


class ConfigValidator:
    """Validates configuration against schema and performs integrity checks."""
    
    def __init__(self, base_path: Optional[str] = None):
        """Initialize validator with base path for resource checks.
        
        Args:
            base_path: Base directory for finding pattern packs and models
        """
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.schema = self._load_schema()
        
    def _load_schema(self) -> Dict:
        """Load the configuration schema."""
        schema_path = Path(__file__).parent / "config.schema.json"
        try:
            with open(schema_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def validate_schema(self, config: Dict) -> Tuple[bool, List[str]]:
        """Validate configuration against JSON schema.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if not self.schema:
            return True, ["Schema not found, skipping schema validation"]
        
        if jsonschema is None:
            return True, ["jsonschema package not installed, skipping schema validation"]
        
        errors = []
        try:
            jsonschema.validate(config, self.schema)
            return True, []
        except jsonschema.exceptions.ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
            return False, errors
    
    def check_regex_packs(self, pack_names: List[str]) -> Tuple[bool, List[str]]:
        """Check if specified regex packs exist.
        
        Args:
            pack_names: List of pattern pack names to check
            
        Returns:
            Tuple of (all_exist, list_of_issues)
        """
        issues = []
        pattern_packs_dir = self.base_path / "pattern_packs"
        
        if not pattern_packs_dir.exists():
            return False, [f"Pattern packs directory not found: {pattern_packs_dir}"]
        
        for pack_name in pack_names:
            pack_file = pattern_packs_dir / f"{pack_name}.yaml"
            if not pack_file.exists():
                issues.append(f"Pattern pack not found: {pack_name}.yaml")
        
        return len(issues) == 0, issues
    
    def check_ner_models(self, model_ids: List[str]) -> Tuple[bool, List[str]]:
        """Check if specified NER models are registered.
        
        Args:
            model_ids: List of model IDs to check
            
        Returns:
            Tuple of (all_exist, list_of_issues)
        """
        issues = []
        models_file = self.base_path / "core" / "models.yaml"
        
        if not models_file.exists():
            # If models.yaml doesn't exist, we can't validate
            return True, ["models.yaml not found, skipping model validation"]
        
        try:
            with open(models_file, 'r') as f:
                models_data = yaml.safe_load(f) or {}
            
            registered_models = {model['id'] for model in models_data.get('models', [])}
            
            for model_id in model_ids:
                if model_id not in registered_models:
                    issues.append(f"Model not registered: {model_id}")
        
        except Exception as e:
            return False, [f"Error reading models.yaml: {str(e)}"]
        
        return len(issues) == 0, issues
    
    def validate_integrity(self, config: Dict) -> Tuple[bool, List[str]]:
        """Perform integrity checks on configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        all_issues = []
        
        # Check regex packs if specified
        if 'regex_packs' in config:
            valid, issues = self.check_regex_packs(config['regex_packs'])
            all_issues.extend(issues)
        
        # Check NER models if specified and not in regex_only mode
        if not config.get('regex_only', False) and 'ner_models' in config:
            valid, issues = self.check_ner_models(config['ner_models'])
            all_issues.extend(issues)
        
        # Additional integrity checks
        if config.get('regex_only', False) and config.get('ner_models'):
            all_issues.append("Warning: NER models specified but regex_only is True")
        
        if config.get('min_confidence', 0.5) < 0.0 or config.get('min_confidence', 0.5) > 1.0:
            all_issues.append("min_confidence must be between 0.0 and 1.0")
        
        return len(all_issues) == 0, all_issues
    
    def validate(self, config: Dict) -> Dict:
        """Perform full validation of configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Dictionary with validation results:
                - valid: bool indicating if config is valid
                - schema_valid: bool for schema validation
                - integrity_valid: bool for integrity checks
                - errors: list of error messages
                - warnings: list of warning messages
        """
        result = {
            'valid': True,
            'schema_valid': True,
            'integrity_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Schema validation
        schema_valid, schema_errors = self.validate_schema(config)
        result['schema_valid'] = schema_valid
        if not schema_valid:
            result['errors'].extend(schema_errors)
            result['valid'] = False
        
        # Integrity validation
        integrity_valid, integrity_issues = self.validate_integrity(config)
        result['integrity_valid'] = integrity_valid
        
        # Separate warnings from errors
        for issue in integrity_issues:
            if issue.startswith("Warning:"):
                result['warnings'].append(issue)
            else:
                result['errors'].append(issue)
                result['valid'] = False
        
        return result