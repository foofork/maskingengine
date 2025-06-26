#!/usr/bin/env python
"""Example of using MaskingEngine REST API."""

import json
import requests
from typing import Dict, Any

# API configuration
API_BASE_URL = "http://localhost:8000"


def sanitize_text(content: str, **options) -> Dict[str, Any]:
    """Sanitize text content using the API."""
    response = requests.post(
        f"{API_BASE_URL}/sanitize", json={"content": content, "format": "text", **options}
    )
    response.raise_for_status()
    return response.json()


def rehydrate_text(sanitized_content: str, mask_map: Dict[str, Any]) -> str:
    """Rehydrate sanitized content using the API."""
    response = requests.post(
        f"{API_BASE_URL}/rehydrate",
        json={"sanitized_content": sanitized_content, "mask_map": mask_map, "format": "text"},
    )
    response.raise_for_status()
    return response.json()["original_content"]


def main():
    """Demonstrate API usage with various examples."""
    print("🚀 MaskingEngine API Example\n")

    # Example 1: Basic text sanitization
    print("Example 1: Basic Text Sanitization")
    print("-" * 40)

    text = "Please contact John Doe at john.doe@example.com or call 555-123-4567."
    result = sanitize_text(text)

    print(f"Original: {text}")
    print(f"Sanitized: {result['sanitized_content']}")
    print(f"Detected {result['detection_count']} PII entities")
    print(f"Mask map: {json.dumps(result['mask_map'], indent=2)}\n")

    # Example 2: JSON content sanitization
    print("Example 2: JSON Content Sanitization")
    print("-" * 40)

    json_data = {
        "user": {
            "name": "Jane Smith",
            "email": "jane.smith@company.com",
            "phone": "+1-555-987-6543",
            "address": "123 Main St, New York, NY",
        },
        "notes": "Customer since 2020",
    }

    response = requests.post(
        f"{API_BASE_URL}/sanitize", json={"content": json.dumps(json_data), "format": "json"}
    )
    json_result = response.json()

    print(f"Original JSON: {json.dumps(json_data, indent=2)}")
    print(f"Sanitized JSON: {json_result['sanitized_content']}")
    print(f"Detected {json_result['detection_count']} PII entities\n")

    # Example 3: Custom configuration
    print("Example 3: Custom Configuration")
    print("-" * 40)

    text_custom = "Contact CEO Tim Cook at tcook@apple.com about the iPhone project."
    result_custom = sanitize_text(
        text_custom,
        min_confidence=0.8,
        whitelist=["iPhone", "Apple"],
        placeholder_prefix="REDACTED_",
        enable_ner=True,
        enable_regex=True,
    )

    print(f"Original: {text_custom}")
    print(f"Sanitized: {result_custom['sanitized_content']}")
    print(f"(Note: 'iPhone' and 'Apple' were whitelisted)\n")

    # Example 4: Rehydration
    print("Example 4: Rehydration (Unmasking)")
    print("-" * 40)

    # Use result from Example 1
    restored = rehydrate_text(result["sanitized_content"], result["mask_map"])

    print(f"Sanitized: {result['sanitized_content']}")
    print(f"Restored: {restored}")
    print(f"Match original: {restored == text}\n")

    # Example 5: Error handling
    print("Example 5: Error Handling")
    print("-" * 40)

    try:
        # Invalid format
        response = requests.post(
            f"{API_BASE_URL}/sanitize", json={"content": "test", "format": "invalid_format"}
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Expected error for invalid format: {e.response.json()['detail']}")

    # Health check
    health = requests.get(f"{API_BASE_URL}/health").json()
    print(f"\nAPI Health: {health}")


if __name__ == "__main__":
    print("⚠️  Make sure the API is running: python scripts/run_api.py\n")
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Please start the API server first:")
        print("   python scripts/run_api.py")
