"""Integration tests for the complete sanitization workflow following TDD principles."""

import pytest
from maskingengine import sanitize, rehydrate, SanitizerConfig


class TestSanitizerIntegration:
    """Integration tests for the sanitizer system."""

    # Basic Sanitization Tests
    def test_sanitize_basic_text(self):
        """Test basic text sanitization with default config."""
        original = "Contact John Doe at john.doe@example.com or 555-123-4567"

        masked, rehydration_map = sanitize(original)

        # Verify PII is masked
        assert "john.doe@example.com" not in masked
        assert "555-123-4567" not in masked
        assert "<<EMAIL_" in masked
        assert "<<PHONE_" in masked

        # Verify rehydration works
        restored = rehydrate(masked, rehydration_map)
        assert restored == original

    def test_sanitize_with_whitelist(self):
        """Test sanitization with whitelist configuration."""
        original = "Contact Acme Corp at info@acme.com about Project Phoenix"
        config = {"whitelist": ["Acme Corp", "Project Phoenix"]}

        masked, rehydration_map = sanitize(original, config)

        # Whitelisted items should not be masked
        assert "Acme Corp" in masked
        assert "Project Phoenix" in masked
        # Email should still be masked
        assert "info@acme.com" not in masked
        assert "<<EMAIL_" in masked

    def test_sanitize_regex_only(self):
        """Test sanitization with only regex detection enabled."""
        original = "John Smith's email is john@test.com"
        config = {"enable_ner": False, "enable_regex": True}

        masked, rehydration_map = sanitize(original, config)

        # Name should not be detected (NER disabled)
        assert "John Smith" in masked
        # Email should be detected (regex enabled)
        assert "john@test.com" not in masked
        assert "<<EMAIL_" in masked

    def test_sanitize_ner_only(self):
        """Test sanitization with only NER detection enabled."""
        original = "Contact John Smith at john@test.com"
        config = {"enable_regex": False, "enable_ner": True}

        masked, rehydration_map = sanitize(original, config)

        # Name should be detected (NER enabled)
        # Note: This test assumes NER model is loaded
        # In practice, might need to mock or skip if model not available

        # Email should not be detected (regex disabled)
        assert "john@test.com" in masked

    def test_custom_placeholders(self):
        """Test custom placeholder format."""
        original = "Email: test@example.com"
        config = {"placeholder_prefix": "{{", "placeholder_suffix": "}}"}

        masked, rehydration_map = sanitize(original, config)

        assert "{{EMAIL_" in masked
        assert "}}" in masked
        assert "<<" not in masked
        assert ">>" not in masked

    # Content Type Tests
    def test_sanitize_json_content(self):
        """Test JSON content sanitization."""
        original = """{
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1-555-123-4567"
        }"""

        masked, rehydration_map = sanitize(original, content_type="json")

        # Should parse and mask JSON content
        assert "john@example.com" not in masked
        assert "+1-555-123-4567" not in masked
        assert "<<EMAIL_" in masked
        assert "<<PHONE_" in masked

        # Should maintain JSON structure
        assert "{" in masked
        assert "}" in masked
        assert '"name"' in masked
        assert '"email"' in masked

    def test_sanitize_html_content(self):
        """Test HTML content sanitization."""
        original = """<div>
            <p>Contact: <a href="mailto:john@example.com">John Doe</a></p>
            <p>Phone: 555-123-4567</p>
        </div>"""

        masked, rehydration_map = sanitize(original, content_type="html")

        # Should extract and mask text from HTML
        assert "john@example.com" not in masked
        assert "555-123-4567" not in masked

    # Error Handling Tests
    def test_max_input_length_exceeded(self):
        """Test that exceeding max input length raises error."""
        config = {"max_input_characters": 10}
        long_text = "a" * 20

        with pytest.raises(ValueError) as exc_info:
            sanitize(long_text, config)

        assert "exceeds maximum length" in str(exc_info.value)

    def test_invalid_json_content(self):
        """Test that invalid JSON raises appropriate error."""
        invalid_json = '{"name": "John", "email"'  # Incomplete JSON

        with pytest.raises(ValueError) as exc_info:
            sanitize(invalid_json, content_type="json")

        assert "Invalid JSON" in str(exc_info.value)

    # Configuration Tests
    def test_confidence_threshold(self):
        """Test NER confidence threshold configuration."""
        original = "Contact person at location"  # Ambiguous entities

        # High threshold - might not detect
        config_high = {"confidence_threshold": 0.95}
        masked_high, _ = sanitize(original, config_high)

        # Low threshold - more likely to detect
        config_low = {"confidence_threshold": 0.5}
        masked_low, _ = sanitize(original, config_low)

        # Lower threshold should detect more (or equal) entities
        # Exact behavior depends on model
        assert len(masked_low) >= len(masked_high)

    # Complex Scenarios
    def test_multilingual_content(self):
        """Test sanitization of multilingual content."""
        original = "Contact María García at maria@ejemplo.es or +34 612 345 678"

        masked, rehydration_map = sanitize(original)

        # Should detect email and phone regardless of language
        assert "maria@ejemplo.es" not in masked
        assert "+34 612 345 678" not in masked

        restored = rehydrate(masked, rehydration_map)
        assert restored == original

    def test_repeated_pii(self):
        """Test handling of repeated PII values."""
        original = "Email john@test.com twice: john@test.com"

        masked, rehydration_map = sanitize(original)

        # Both instances should be masked with same placeholder
        assert masked.count("<<EMAIL_") == 2
        assert "john@test.com" not in masked

        # Should have only one entry in rehydration map
        email_placeholders = [k for k in rehydration_map.keys() if "EMAIL" in k]
        assert len(email_placeholders) == 1

    def test_mixed_pii_types(self):
        """Test detection of multiple PII types in complex text."""
        original = """
        Dear John Smith,
        
        Please contact our office at:
        Email: info@company.com
        Phone: +1-555-123-4567
        Address: 123 Main St, New York
        IP: 192.168.1.100
        
        Credit Card: 4111111111111111
        
        Best regards,
        Jane Doe
        CEO, Acme Corporation
        """

        masked, rehydration_map = sanitize(original)

        # Verify various PII types are detected
        assert "info@company.com" not in masked
        assert "+1-555-123-4567" not in masked
        assert "192.168.1.100" not in masked
        assert "4111111111111111" not in masked

        # Verify names are detected (if NER is working)
        # This depends on NER model availability

        # Verify rehydration restores everything
        restored = rehydrate(masked, rehydration_map)
        assert restored == original

    def test_performance_large_text(self):
        """Test performance with large text input."""
        # Generate large text with some PII
        large_text = "Lorem ipsum " * 1000
        large_text += "Contact john@example.com for details. "
        large_text += "Call 555-123-4567. " * 10

        import time

        start = time.time()
        masked, rehydration_map = sanitize(large_text)
        duration = time.time() - start

        # Should complete in reasonable time
        assert duration < 5.0  # 5 seconds max

        # Should still detect PII
        assert "john@example.com" not in masked
        assert "555-123-4567" not in masked
