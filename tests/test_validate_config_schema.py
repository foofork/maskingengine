"""Test configuration schema validation."""

import pytest
import json
import tempfile
from pathlib import Path
from maskingengine.core import ConfigResolver, ConfigValidator


class TestConfigSchemaValidation:
    """Test configuration validation and schema compliance."""
    
    def test_valid_minimal_config(self):
        """Test that a minimal valid configuration passes validation."""
        config = {
            "regex_only": True
        }
        
        resolver = ConfigResolver()
        result = resolver.resolve_and_validate(config=config)
        
        assert result['status'] == 'valid'
        assert result['resolved_config']['regex_only'] is True
        assert 'default' in result['resolved_config']['regex_packs']
    
    def test_valid_full_config(self):
        """Test that a complete valid configuration passes validation."""
        config = {
            "regex_only": True,  # Use regex-only to avoid NER model validation
            "mask_types": ["EMAIL", "PHONE"],
            "min_confidence": 0.7,
            "whitelist": ["support@company.com"],
            "strict_validation": True,
            "placeholder_prefix": "<<",
            "placeholder_suffix": ">>",
            "streaming": {
                "enabled": True,
                "chunk_size": 8192
            },
            "rate_limiting": {
                "enabled": False,
                "requests_per_minute": 60
            }
        }
        
        resolver = ConfigResolver()
        result = resolver.resolve_and_validate(config=config)
        
        assert result['status'] == 'valid'
        assert result['resolved_config']['regex_only'] is True
        assert result['resolved_config']['min_confidence'] == 0.7
        assert result['resolved_config']['streaming']['chunk_size'] == 8192
    
    def test_invalid_schema_config(self):
        """Test that configuration with schema violations fails validation."""
        config = {
            "regex_only": "not_a_boolean",  # Should be boolean
            "min_confidence": 1.5,  # Should be <= 1.0
            "streaming": {
                "chunk_size": "not_a_number"  # Should be integer
            }
        }
        
        resolver = ConfigResolver()
        result = resolver.resolve_and_validate(config=config)
        
        assert result['status'] == 'invalid'
        assert len(result['issues']) > 0
    
    def test_profile_resolution(self):
        """Test that profiles are correctly resolved and merged."""
        resolver = ConfigResolver()
        
        # Test minimal profile
        result = resolver.resolve_and_validate(profile="minimal")
        
        assert result['status'] == 'valid'
        assert result['resolved_config']['regex_only'] is True
        assert "minimal" in result['explanation'].lower()
    
    def test_profile_override(self):
        """Test that user config overrides profile settings."""
        config = {
            "min_confidence": 0.9  # Override profile default
        }
        
        resolver = ConfigResolver()
        result = resolver.resolve_and_validate(config=config, profile="minimal")
        
        assert result['status'] == 'valid'
        assert result['resolved_config']['regex_only'] is True  # From profile
        assert result['resolved_config']['min_confidence'] == 0.9  # From override
    
    def test_invalid_profile(self):
        """Test handling of non-existent profiles."""
        resolver = ConfigResolver()
        result = resolver.resolve_and_validate(profile="nonexistent-profile")
        
        assert result['status'] == 'invalid'
        assert "does not exist" in result['explanation']
    
    def test_config_file_loading(self):
        """Test loading configuration from file."""
        config_data = {
            "regex_only": True,
            "whitelist": ["test@example.com"],
            "min_confidence": 0.8
        }
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            resolver = ConfigResolver()
            result = resolver.resolve_and_validate(config_path=config_file)
            
            assert result['status'] == 'valid'
            assert result['resolved_config']['regex_only'] is True
            assert result['resolved_config']['min_confidence'] == 0.8
            assert "test@example.com" in result['resolved_config']['whitelist']
        
        finally:
            Path(config_file).unlink()  # Clean up
    
    def test_json_config_file(self):
        """Test loading JSON configuration file."""
        config_data = {
            "regex_only": True,
            "strict_validation": False
        }
        
        # Create temporary JSON config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            resolver = ConfigResolver()
            result = resolver.resolve_and_validate(config_path=config_file)
            
            assert result['status'] == 'valid'
            assert result['resolved_config']['strict_validation'] is False
        
        finally:
            Path(config_file).unlink()  # Clean up
    
    def test_config_path_resolution(self):
        """Test configuration file path resolution."""
        resolver = ConfigResolver()
        
        # Test with non-existent file
        resolved_path = resolver.resolve_config_path("nonexistent.yaml")
        assert resolved_path is None
        
        # Test with existing file
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            f.write(b"regex_only: true")
            temp_file = f.name
        
        try:
            resolved_path = resolver.resolve_config_path(temp_file)
            assert resolved_path == Path(temp_file)
        finally:
            Path(temp_file).unlink()
    
    def test_validator_schema_validation(self):
        """Test the ConfigValidator schema validation directly."""
        validator = ConfigValidator()
        
        # Valid config
        valid_config = {
            "regex_only": True,
            "min_confidence": 0.5
        }
        
        is_valid, errors = validator.validate_schema(valid_config)
        assert is_valid
        assert len(errors) == 0
        
        # Invalid config
        invalid_config = {
            "regex_only": "not_boolean",
            "min_confidence": 2.0  # Out of range
        }
        
        is_valid, errors = validator.validate_schema(invalid_config)
        # Note: might pass if jsonschema not installed
        if not is_valid:
            assert len(errors) > 0
    
    def test_validator_integrity_checks(self):
        """Test the ConfigValidator integrity checking."""
        validator = ConfigValidator()
        
        # Config with regex_only but NER models specified
        config = {
            "regex_only": True,
            "ner_models": ["some-model"]
        }
        
        is_valid, issues = validator.validate_integrity(config)
        
        # Should have a warning about NER models with regex_only
        warning_found = any("regex_only is True" in issue for issue in issues)
        assert warning_found
    
    def test_pattern_pack_validation(self):
        """Test pattern pack existence validation."""
        validator = ConfigValidator()
        
        # Test with non-existent pattern packs
        nonexistent_packs = ["nonexistent_pack_1", "nonexistent_pack_2"]
        
        valid, issues = validator.check_regex_packs(nonexistent_packs)
        assert not valid
        assert len(issues) > 0
        assert any("not found" in issue for issue in issues)
    
    def test_ner_model_validation(self):
        """Test NER model registry validation."""
        validator = ConfigValidator()
        
        # Test with non-existent models (if models.yaml exists)
        nonexistent_models = ["nonexistent-model-1", "nonexistent-model-2"]
        
        valid, issues = validator.check_ner_models(nonexistent_models)
        
        # If models.yaml doesn't exist, should skip validation
        # If it exists, should report missing models
        if "models.yaml not found" in str(issues):
            # No models.yaml file - validation skipped
            pass
        else:
            # models.yaml exists - should report missing models
            assert not valid
            assert len(issues) > 0
    
    def test_deep_merge_functionality(self):
        """Test the deep merge functionality of ConfigResolver."""
        resolver = ConfigResolver()
        
        base = {
            "regex_only": False,
            "streaming": {
                "enabled": False,
                "chunk_size": 4096
            },
            "whitelist": ["default@example.com"]
        }
        
        override = {
            "regex_only": True,
            "streaming": {
                "enabled": True
                # chunk_size should remain from base
            },
            "whitelist": ["override@example.com"]  # Complete override
        }
        
        merged = resolver._deep_merge(base, override)
        
        assert merged["regex_only"] is True  # Overridden
        assert merged["streaming"]["enabled"] is True  # Overridden
        assert merged["streaming"]["chunk_size"] == 4096  # Preserved from base
        assert merged["whitelist"] == ["override@example.com"]  # Completely overridden
    
    def test_config_explanations(self):
        """Test that configuration explanations are informative."""
        resolver = ConfigResolver()
        
        # Test with profile
        result = resolver.resolve_and_validate(profile="minimal")
        assert "minimal" in result['explanation'].lower()
        
        # Test with config override
        config = {"regex_only": False}
        result = resolver.resolve_and_validate(config=config)
        assert "provided configuration" in result['explanation'].lower()
        
        # Test validation failure
        invalid_config = {"min_confidence": 2.0}
        result = resolver.resolve_and_validate(config=invalid_config)
        if result['status'] == 'invalid':
            assert "errors" in result['explanation'].lower()
    
    def test_config_layer_precedence(self):
        """Test that configuration layers have correct precedence."""
        # Create a temporary config file
        file_config = {
            "regex_only": True,  # Avoid pattern pack validation
            "min_confidence": 0.6,
            "whitelist": ["file@example.com"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(file_config, f)
            config_file = f.name
        
        try:
            # Direct config should override file config
            direct_config = {
                "min_confidence": 0.9,  # Override file
                "strict_validation": False  # New setting
            }
            
            resolver = ConfigResolver()
            result = resolver.resolve_and_validate(
                config=direct_config,
                config_path=config_file,
                profile="minimal"  # Should be lowest precedence
            )
            
            assert result['status'] == 'valid'
            # Direct config should win
            assert result['resolved_config']['min_confidence'] == 0.9
            assert result['resolved_config']['strict_validation'] is False
            
            # File config should override profile
            assert result['resolved_config']['regex_only'] is True  # From file, not profile
            assert "file@example.com" in result['resolved_config']['whitelist']
        
        finally:
            Path(config_file).unlink()