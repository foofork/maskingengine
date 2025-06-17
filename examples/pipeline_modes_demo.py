#!/usr/bin/env python3
"""Demonstration of regex-only vs full pipeline modes in MaskingEngine."""

from maskingengine import Sanitizer, Config
import time


def demo_pipeline_modes():
    """Demonstrate the difference between regex-only and full pipeline modes."""
    
    # Sample text with various PII types
    test_text = """
    Patient: John Smith (DOB: 01/15/1980)
    Medical Record: MRN-123456
    Contact: john.smith@hospital.com, (555) 123-4567
    SSN: 123-45-6789
    Doctor: Dr. Sarah Johnson at Mercy Hospital
    Insurance ID: INS-987654
    Address: 123 Main St, Boston, MA 02134
    """
    
    print("=== MaskingEngine Pipeline Modes Demo ===\n")
    print("Original Text:")
    print(test_text)
    print("-" * 60)
    
    # 1. Regex-only mode (fastest, pattern-based)
    print("\n1. REGEX-ONLY MODE")
    print("   - Uses only predefined regex patterns")
    print("   - Fastest performance")
    print("   - No ML model required")
    print("   - Best for structured data (emails, phones, SSNs, etc.)\n")
    
    config_regex = Config(regex_only=True, pattern_packs=["default", "healthcare"])
    sanitizer_regex = Sanitizer(config_regex)
    
    start_time = time.time()
    masked_regex, mask_map_regex = sanitizer_regex.sanitize(test_text)
    regex_time = time.time() - start_time
    
    print(f"Masked Text:\n{masked_regex}")
    print(f"\nDetected {len(mask_map_regex)} PII entities in {regex_time:.4f} seconds:")
    for placeholder, value in sorted(mask_map_regex.items()):
        print(f"  • {placeholder} → {value}")
    
    print("\n" + "-" * 60)
    
    # 2. Full pipeline mode (regex + NER)
    print("\n2. FULL PIPELINE MODE (Regex + NER)")
    print("   - Uses regex patterns AND ML-based NER")
    print("   - Can detect names, organizations, locations")
    print("   - More comprehensive but slower")
    print("   - Requires NER model (if available)\n")
    
    config_full = Config(regex_only=False, pattern_packs=["default", "healthcare"])
    sanitizer_full = Sanitizer(config_full)
    
    start_time = time.time()
    masked_full, mask_map_full = sanitizer_full.sanitize(test_text)
    full_time = time.time() - start_time
    
    print(f"Masked Text:\n{masked_full}")
    print(f"\nDetected {len(mask_map_full)} PII entities in {full_time:.4f} seconds:")
    for placeholder, value in sorted(mask_map_full.items()):
        print(f"  • {placeholder} → {value}")
    
    print("\n" + "-" * 60)
    
    # 3. Comparison
    print("\n3. COMPARISON")
    print(f"   Regex-only mode: {len(mask_map_regex)} entities in {regex_time:.4f}s")
    print(f"   Full pipeline:   {len(mask_map_full)} entities in {full_time:.4f}s")
    
    if regex_time > 0:
        speedup = full_time / regex_time
        print(f"   Speedup factor:  {speedup:.1f}x")
    
    # Show what additional entities NER might detect
    regex_placeholders = set(mask_map_regex.values())
    full_placeholders = set(mask_map_full.values())
    ner_only = full_placeholders - regex_placeholders
    
    if ner_only:
        print(f"\n   Additional entities detected by NER:")
        for entity in ner_only:
            print(f"     • {entity}")
    else:
        print("\n   (No additional entities detected by NER - model may not be loaded)")
    
    print("\n" + "=" * 60)
    print("\nRECOMMENDATIONS:")
    print("• Use regex-only mode for:")
    print("  - High-performance requirements")
    print("  - Structured data (emails, phones, IDs)")
    print("  - When NER models aren't available")
    print("  - Consistent, predictable patterns")
    print("\n• Use full pipeline mode for:")
    print("  - Maximum coverage")
    print("  - Unstructured text")
    print("  - When names/orgs/locations are critical")
    print("  - When accuracy > speed")


if __name__ == "__main__":
    demo_pipeline_modes()