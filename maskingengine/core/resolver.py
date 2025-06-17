"""Configuration resolver module that merges defaults, profiles, and user overrides."""

import os
import json
from pathlib import Path
from typing import Dict, Optional, Any
import yaml

from .validator import ConfigValidator


class ConfigResolver:
    """Resolves and validates configuration from multiple sources."""
    
    # Default configuration values
    DEFAULTS = {
        'regex_packs': ['default'],
        'ner_models': [],
        'mask_types': [],  # Empty means mask all detected types
        'regex_only': False,
        'min_confidence': 0.5,
        'whitelist': [],
        'strict_validation': True,
        'placeholder_prefix': '<<',
        'placeholder_suffix': '>>',
        'streaming': {
            'enabled': False,
            'chunk_size': 4096
        },
        'rate_limiting': {
            'enabled': False,
            'requests_per_minute': 60
        }
    }
    
    def __init__(self, base_path: Optional[str] = None):
        """Initialize resolver with base path.
        
        Args:
            base_path: Base directory for finding profiles and resources
        """
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.validator = ConfigValidator(self.base_path)
        self.profiles = self._load_profiles()
    
    def _load_profiles(self) -> Dict[str, Dict]:
        """Load available configuration profiles."""
        profiles_file = Path(__file__).parent / "profiles.yaml"
        if not profiles_file.exists():
            return {}
        
        try:
            with open(profiles_file, 'r') as f:
                profiles_data = yaml.safe_load(f) or {}
            # Remove description from each profile before returning
            return {
                name: {k: v for k, v in profile.items() if k != 'description'}
                for name, profile in profiles_data.items()
            }
        except Exception as e:
            print(f"Warning: Could not load profiles: {e}")
            return {}
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries, with override taking precedence.
        
        Args:
            base: Base dictionary
            override: Dictionary with values to override
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._deep_merge(result[key], value)
            else:
                # Override the value
                result[key] = value
        
        return result
    
    def resolve_config_path(self, config_path: Optional[str] = None) -> Optional[Path]:
        """Resolve configuration file path from multiple sources.
        
        Args:
            config_path: Explicit config path (highest priority)
            
        Returns:
            Path to config file or None if not found
        """
        # Priority order:
        # 1. Explicit path provided
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path
        
        # 2. Environment variable
        env_path = os.environ.get('PII_SANITIZE_CONFIG')
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path
        
        # 3. Local project file
        local_path = Path('./pii-sanitize.config.yaml')
        if local_path.exists():
            return local_path
        
        # 4. Global config file
        global_path = Path.home() / '.config' / 'pii-sanitize' / 'config.yaml'
        if global_path.exists():
            return global_path
        
        return None
    
    def load_user_config(self, config_path: Optional[str] = None) -> Dict:
        """Load user configuration from file.
        
        Args:
            config_path: Path to config file or None to auto-discover
            
        Returns:
            User configuration dictionary
        """
        resolved_path = self.resolve_config_path(config_path)
        if not resolved_path:
            return {}
        
        try:
            with open(resolved_path, 'r') as f:
                if resolved_path.suffix == '.json':
                    return json.load(f)
                else:
                    return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load config from {resolved_path}: {e}")
            return {}
    
    def resolve_and_validate(self, config: Optional[Dict] = None, 
                           config_path: Optional[str] = None,
                           profile: Optional[str] = None) -> Dict:
        """Resolve and validate configuration from all sources.
        
        Args:
            config: Direct configuration dictionary (highest priority)
            config_path: Path to configuration file
            profile: Name of profile to use as base
            
        Returns:
            Dictionary with:
                - status: 'valid' or 'invalid'
                - resolved_config: Fully merged configuration
                - issues: List of validation errors/warnings
                - explanation: Human-readable summary
        """
        # Start with defaults
        resolved = self.DEFAULTS.copy()
        
        # Layer 1: Apply profile if specified
        if profile:
            if profile in self.profiles:
                resolved = self._deep_merge(resolved, self.profiles[profile])
            else:
                return {
                    'status': 'invalid',
                    'resolved_config': {},
                    'issues': [f"Profile '{profile}' not found"],
                    'explanation': f"Configuration profile '{profile}' does not exist."
                }
        
        # Layer 2: Apply user config from file
        if config_path or not config:
            user_config = self.load_user_config(config_path)
            if user_config:
                # Check if user config specifies a profile
                if 'profile' in user_config and not profile:
                    profile_name = user_config['profile']
                    if profile_name in self.profiles:
                        resolved = self._deep_merge(resolved, self.profiles[profile_name])
                    user_config = {k: v for k, v in user_config.items() if k != 'profile'}
                
                resolved = self._deep_merge(resolved, user_config)
        
        # Layer 3: Apply direct config overrides
        if config:
            resolved = self._deep_merge(resolved, config)
        
        # Validate the resolved configuration
        validation_result = self.validator.validate(resolved)
        
        # Build explanation
        explanation_parts = []
        if profile:
            explanation_parts.append(f"Using profile '{profile}'")
        if config_path:
            explanation_parts.append(f"Loaded config from {config_path}")
        elif config:
            explanation_parts.append("Using provided configuration")
        
        if validation_result['valid']:
            explanation_parts.append("Configuration is valid")
        else:
            explanation_parts.append("Configuration has errors")
        
        explanation = ". ".join(explanation_parts) + "."
        
        return {
            'status': 'valid' if validation_result['valid'] else 'invalid',
            'resolved_config': resolved if validation_result['valid'] else {},
            'issues': validation_result['errors'] + validation_result['warnings'],
            'explanation': explanation
        }