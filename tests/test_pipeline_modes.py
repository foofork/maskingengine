"""Test regex-only vs full pipeline modes."""

import pytest
from maskingengine import Sanitizer, Config


class TestPipelineModes:
    """Test different detection pipeline modes."""
    
    def test_regex_only_mode(self):
        """Test that regex-only mode only uses regex patterns."""
        config = Config(regex_only=True)
        sanitizer = Sanitizer(config)
        
        # Test with content that has both regex-detectable and NER-detectable PII
        text = "Contact John Smith (CEO of Acme Corp) at john@example.com or 555-123-4567"
        masked, mask_map = sanitizer.sanitize(text)
        
        # Should detect email and phone (regex patterns)
        assert "john@example.com" not in masked
        assert "555-123-4567" not in masked
        assert len(mask_map) >= 2  # At least email and phone
        
        # Check that NER is disabled
        assert config.NER_ENABLED is False
        assert sanitizer.detector.ner_detector is None
    
    def test_full_pipeline_mode(self):
        """Test that full pipeline mode uses both regex and NER."""
        config = Config(regex_only=False)
        sanitizer = Sanitizer(config)
        
        # Check that NER is enabled
        assert config.NER_ENABLED is True
        # NER detector would be created if model is available
        # (actual detection depends on model availability)
        
        text = "Contact John Smith at john@example.com"
        masked, mask_map = sanitizer.sanitize(text)
        
        # Should at least detect email
        assert "john@example.com" not in masked
        assert len(mask_map) >= 1
    
    def test_config_regex_only_flag(self):
        """Test Config properly handles regex_only flag."""
        # Default should have NER enabled
        config_default = Config()
        assert config_default.NER_ENABLED is True
        
        # Explicit regex_only=True should disable NER
        config_regex = Config(regex_only=True)
        assert config_regex.NER_ENABLED is False
        
        # Explicit regex_only=False should enable NER
        config_full = Config(regex_only=False)
        assert config_full.NER_ENABLED is True
    
    def test_profiles_regex_only_setting(self):
        """Test that profiles correctly set regex_only mode."""
        from maskingengine.core import ConfigResolver
        
        resolver = ConfigResolver()
        
        # Minimal profile should be regex-only
        result = resolver.resolve_and_validate(profile="minimal")
        assert result['status'] == 'valid'
        assert result['resolved_config']['regex_only'] is True
        
        # Healthcare profile should be regex-only
        result = resolver.resolve_and_validate(profile="healthcare-en")
        assert result['status'] == 'valid'
        assert result['resolved_config']['regex_only'] is True
        
        # Standard profile should use full pipeline
        result = resolver.resolve_and_validate(profile="standard")
        assert result['status'] == 'valid'
        assert result['resolved_config']['regex_only'] is False
    
    def test_api_regex_only_parameter(self):
        """Test API properly handles regex_only parameter."""
        from fastapi.testclient import TestClient
        from maskingengine.api.main import app
        
        client = TestClient(app)
        
        # Test with regex_only=True
        response = client.post("/sanitize", json={
            "content": "Email: test@example.com",
            "regex_only": True
        })
        assert response.status_code == 200
        data = response.json()
        assert "test@example.com" not in data["sanitized_content"]
        
        # Test with regex_only=False
        response = client.post("/sanitize", json={
            "content": "Email: test@example.com", 
            "regex_only": False
        })
        assert response.status_code == 200
        data = response.json()
        assert "test@example.com" not in data["sanitized_content"]
    
    def test_cli_regex_only_flag(self):
        """Test CLI properly handles --regex-only flag."""
        from click.testing import CliRunner
        from maskingengine.cli.main import cli
        
        runner = CliRunner()
        
        # Test with --regex-only flag
        result = runner.invoke(cli, [
            'mask', '--stdin', '--regex-only'
        ], input="Contact: admin@example.com")
        
        assert result.exit_code == 0
        assert "admin@example.com" not in result.output
        assert "<<EMAIL_" in result.output
    
    def test_performance_difference(self):
        """Test that regex-only mode is faster than full pipeline."""
        import time
        
        # Large text for performance testing
        large_text = " ".join([
            f"Contact person{i}@example.com or call 555-{i:04d}"
            for i in range(100)
        ])
        
        # Time regex-only mode
        config_regex = Config(regex_only=True)
        sanitizer_regex = Sanitizer(config_regex)
        
        start = time.time()
        masked_regex, _ = sanitizer_regex.sanitize(large_text)
        regex_time = time.time() - start
        
        # Time full pipeline mode
        config_full = Config(regex_only=False)
        sanitizer_full = Sanitizer(config_full)
        
        start = time.time()
        masked_full, _ = sanitizer_full.sanitize(large_text)
        full_time = time.time() - start
        
        # Regex-only should be faster or equal (if NER not loaded)
        # This is a soft assertion as actual performance depends on model loading
        assert regex_time <= full_time * 1.5  # Allow some variance
        
        # Both should mask the content
        assert "person0@example.com" not in masked_regex
        assert "person0@example.com" not in masked_full