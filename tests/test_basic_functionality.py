"""Basic functionality tests for MaskingEngine."""

import pytest
from maskingengine import Sanitizer, Config, Rehydrator


class TestBasicFunctionality:
    """Test basic MaskingEngine functionality."""
    
    def test_import(self):
        """Test that package can be imported."""
        assert Sanitizer is not None
        assert Config is not None
        assert Rehydrator is not None
    
    def test_regex_email_detection(self):
        """Test email detection with regex-only mode."""
        config = Config(regex_only=True)
        sanitizer = Sanitizer(config)
        
        text = "Contact john@example.com for details"
        masked, mask_map = sanitizer.sanitize(text)
        
        assert "john@example.com" not in masked
        assert "<<EMAIL_" in masked
        assert len(mask_map) == 1
        
    def test_regex_phone_detection(self):
        """Test phone detection with regex-only mode."""
        config = Config(regex_only=True)
        sanitizer = Sanitizer(config)
        
        text = "Call me at 555-123-4567"
        masked, mask_map = sanitizer.sanitize(text)
        
        assert "555-123-4567" not in masked
        assert "<<PHONE_" in masked
        assert len(mask_map) == 1
    
    def test_multiple_pii_detection(self):
        """Test detection of multiple PII types."""
        config = Config(regex_only=True)
        sanitizer = Sanitizer(config)
        
        text = "Email john@example.com or call 555-123-4567"
        masked, mask_map = sanitizer.sanitize(text)
        
        assert "john@example.com" not in masked
        assert "555-123-4567" not in masked
        assert "<<EMAIL_" in masked
        assert "<<PHONE_" in masked
        assert len(mask_map) == 2
    
    def test_rehydration(self):
        """Test basic rehydration functionality."""
        config = Config(regex_only=True)
        sanitizer = Sanitizer(config)
        rehydrator = Rehydrator()
        
        original = "Contact john@example.com"
        masked, mask_map = sanitizer.sanitize(original)
        rehydrated = rehydrator.rehydrate(masked, mask_map)
        
        assert rehydrated == original
    
    def test_no_pii_text(self):
        """Test text with no PII remains unchanged."""
        config = Config(regex_only=True)
        sanitizer = Sanitizer(config)
        
        text = "This is a simple text with no PII"
        masked, mask_map = sanitizer.sanitize(text)
        
        assert masked == text
        assert len(mask_map) == 0
    
    def test_whitelist(self):
        """Test whitelist functionality."""
        config = Config(
            regex_only=True,
            whitelist=["support@company.com"]
        )
        sanitizer = Sanitizer(config)
        
        text = "Contact support@company.com or john@example.com"
        masked, mask_map = sanitizer.sanitize(text)
        
        assert "support@company.com" in masked  # Whitelisted
        assert "john@example.com" not in masked  # Not whitelisted
        assert len(mask_map) == 1