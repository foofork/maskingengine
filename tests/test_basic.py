#!/usr/bin/env python3
"""Basic test to verify MaskingEngine functionality."""

from maskingengine import Sanitizer, Config, Rehydrator

def test_basic_functionality():
    """Test basic sanitization and rehydration."""
    # Test basic sanitization
    original_text = "Please contact John Doe at john.doe@example.com or call 555-123-4567."
    print(f"Original: {original_text}")

    # Sanitize with default config
    sanitizer = Sanitizer()
    masked_text, rehydration_map = sanitizer.sanitize(original_text)
    print(f"\nMasked: {masked_text}")
    print(f"Map: {rehydration_map}")

    # Rehydrate
    rehydrator = Rehydrator()
    restored_text = rehydrator.rehydrate(masked_text, rehydration_map)
    print(f"\nRestored: {restored_text}")

    # Test with whitelist
    config = Config(whitelist=["John Doe"])
    sanitizer2 = Sanitizer(config)
    masked_text2, rehydration_map2 = sanitizer2.sanitize(original_text)
    print(f"\n\nWith whitelist: {masked_text2}")

    # Test JSON
    json_text = '{"name": "Maria Garcia", "email": "maria@example.com", "phone": "+1-555-9876"}'
    masked_json, json_map = sanitizer.sanitize(json_text, format="json")
    print(f"\n\nJSON Original: {json_text}")
    print(f"JSON Masked: {masked_json}")

    print("\nBasic tests completed!")
    
    # Basic assertions to make it a proper test
    assert masked_text != original_text
    assert restored_text == original_text
    assert len(rehydration_map) > 0

if __name__ == "__main__":
    test_basic_functionality()