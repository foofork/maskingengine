#!/usr/bin/env python3
"""Basic test to verify MaskingEngine functionality."""

from maskingengine import sanitize, rehydrate

# Test basic sanitization
original_text = "Please contact John Doe at john.doe@example.com or call 555-123-4567."
print(f"Original: {original_text}")

# Sanitize with default config
masked_text, rehydration_map = sanitize(original_text)
print(f"\nMasked: {masked_text}")
print(f"Map: {rehydration_map}")

# Rehydrate
restored_text = rehydrate(masked_text, rehydration_map)
print(f"\nRestored: {restored_text}")

# Test with whitelist
config = {"whitelist": ["John Doe"]}
masked_text2, rehydration_map2 = sanitize(original_text, config)
print(f"\n\nWith whitelist: {masked_text2}")

# Test JSON
json_text = '{"name": "Maria Garcia", "email": "maria@example.com", "phone": "+1-555-9876"}'
masked_json, json_map = sanitize(json_text, content_type="json")
print(f"\n\nJSON Original: {json_text}")
print(f"JSON Masked: {masked_json}")

print("\nBasic tests completed!")