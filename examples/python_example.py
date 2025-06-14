#!/usr/bin/env python
"""Example of using MaskingEngine Python API directly."""

import json
from maskingengine import sanitize, rehydrate
from maskingengine.core.config import SanitizerConfig


def main():
    """Demonstrate direct Python API usage."""
    print("🚀 MaskingEngine Python API Example\n")
    
    # Example 1: Basic usage with default configuration
    print("Example 1: Basic Usage")
    print("-" * 40)
    
    text = "Contact John Doe at john.doe@example.com or call 555-123-4567."
    result = sanitize(text)
    
    print(f"Original: {text}")
    print(f"Sanitized: {result.sanitized_content}")
    print(f"Mask map: {json.dumps(result.mask_map, indent=2)}")
    
    # Rehydrate
    restored = rehydrate(result.sanitized_content, result.mask_map)
    print(f"Restored: {restored}")
    print(f"Match: {restored == text}\n")
    
    # Example 2: Custom configuration
    print("Example 2: Custom Configuration")
    print("-" * 40)
    
    config = SanitizerConfig(
        min_confidence=0.8,
        placeholder_prefix="REDACTED_",
        whitelist={"Apple", "iPhone"},
        enable_ner=True,
        enable_regex=True,
    )
    
    text2 = "Tim Cook (CEO of Apple) can be reached at tcook@apple.com about iPhone plans."
    result2 = sanitize(text2, config=config)
    
    print(f"Original: {text2}")
    print(f"Sanitized: {result2.sanitized_content}")
    print(f"(Note: 'Apple' and 'iPhone' were whitelisted)\n")
    
    # Example 3: JSON content
    print("Example 3: JSON Content")
    print("-" * 40)
    
    json_data = {
        "user": {
            "name": "Jane Smith",
            "email": "jane.smith@company.com",
            "phone": "+1-555-987-6543",
            "ssn": "123-45-6789"
        },
        "account": {
            "number": "ACC-12345",
            "balance": 1500.00
        }
    }
    
    json_str = json.dumps(json_data, indent=2)
    result3 = sanitize(json_str, format="json")
    
    print(f"Original JSON:\n{json_str}")
    print(f"\nSanitized JSON:\n{result3.sanitized_content}")
    print(f"\nDetected {len(result3.mask_map)} PII entities")
    
    # Restore JSON
    restored_json = rehydrate(result3.sanitized_content, result3.mask_map, format="json")
    restored_data = json.loads(restored_json)
    print(f"\nRestored data matches: {restored_data == json_data}\n")
    
    # Example 4: Regex-only detection (faster)
    print("Example 4: Regex-only Detection")
    print("-" * 40)
    
    config_regex = SanitizerConfig(enable_ner=False, enable_regex=True)
    text4 = "Email: test@example.com, Phone: 555-0123, Name: Bob Johnson"
    result4 = sanitize(text4, config=config_regex)
    
    print(f"Original: {text4}")
    print(f"Sanitized (regex only): {result4.sanitized_content}")
    print(f"(Note: Name not detected without NER)\n")
    
    # Example 5: Batch processing
    print("Example 5: Batch Processing")
    print("-" * 40)
    
    documents = [
        "Customer Alice Brown: alice@example.com",
        "Support ticket from Bob: 555-9876",
        "Payment from card ending 4242",
        "Server IP: 192.168.1.50"
    ]
    
    masked_docs = []
    all_masks = {}
    
    for i, doc in enumerate(documents):
        result = sanitize(doc)
        masked_docs.append(result.sanitized_content)
        # Prefix masks with document ID to avoid collisions
        for k, v in result.mask_map.items():
            all_masks[f"doc{i}_{k}"] = v
    
    print("Batch results:")
    for original, masked in zip(documents, masked_docs):
        print(f"  {original} → {masked}")
    
    print(f"\nTotal PII detected across all documents: {len(all_masks)}\n")
    
    # Example 6: Error handling
    print("Example 6: Error Handling")
    print("-" * 40)
    
    try:
        # Invalid format
        sanitize("test", format="invalid")
    except ValueError as e:
        print(f"Expected error for invalid format: {e}")
    
    try:
        # Invalid configuration
        SanitizerConfig(min_confidence=1.5)  # > 1.0
    except ValueError as e:
        print(f"Expected error for invalid config: {e}")


if __name__ == "__main__":
    main()