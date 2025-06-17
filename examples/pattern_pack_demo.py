#!/usr/bin/env python3
"""
MaskingEngine Pattern Pack System Demonstration

This script demonstrates the YAML pattern pack system that allows users to:
1. Use the default pattern pack with universal and country-specific rules
2. Create custom pattern packs for organization-specific PII
3. Combine multiple pattern packs
4. Benefit from context keyword validation for stronger detection
"""

from maskingengine import Sanitizer, Config

def main():
    print("🧩 MaskingEngine - Pattern Pack System Demo")
    print("=" * 60)
    
    # Demo 1: Default pattern pack
    print("\n📦 Demo 1: Default Pattern Pack")
    print("-" * 40)
    
    config = Config(pattern_packs=["default"])
    sanitizer = Sanitizer(config)
    
    default_tests = [
        ("Universal Email", "Contact support@company.com for help"),
        ("Spanish DNI", "Mi DNI es 12345678Z para identificación"),
        ("German Tax ID", "Steuer-IdNr: 12345 67890 für Steuerzwecke"),
        ("French Phone", "Tél: 01 23 45 67 89 pour contact"),
        ("UK NI Number", "My NI number is AB 12 34 56 C"),
        ("Credit Card", "Payment with card 4111-1111-1111-1111"),
    ]
    
    for desc, text in default_tests:
        print(f"\n{desc}:")
        print(f"  Input:  {text}")
        try:
            masked, mask_map = sanitizer.sanitize(text)
            print(f"  Output: {masked}")
            if mask_map:
                for placeholder, original in mask_map.items():
                    entity_type = placeholder.split('_')[1] if '_' in placeholder else placeholder
                    print(f"    Found {entity_type}: {original}")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Demo 2: Custom pattern pack
    print(f"\n\n📦 Demo 2: Custom Enterprise Pattern Pack")
    print("-" * 40)
    
    config = Config(pattern_packs=["custom"])
    sanitizer = Sanitizer(config)
    
    custom_tests = [
        ("Employee ID", "Employee EMP123456 needs access"),
        ("Project Code", "Working on project PROJ-2024-001"),
        ("Customer ID", "Customer CUST-ABC-123 called today"),
        ("Combined", "Employee EMP987654 assigned to PROJ-2024-002 for CUST-XYZ-456"),
    ]
    
    for desc, text in custom_tests:
        print(f"\n{desc}:")
        print(f"  Input:  {text}")
        try:
            masked, mask_map = sanitizer.sanitize(text)
            print(f"  Output: {masked}")
            if mask_map:
                for placeholder, original in mask_map.items():
                    entity_type = placeholder.split('_')[1] if '_' in placeholder else placeholder
                    print(f"    Found {entity_type}: {original}")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Demo 3: Combined pattern packs
    print(f"\n\n📦 Demo 3: Combined Pattern Packs (Default + Custom)")
    print("-" * 40)
    
    config = Config(pattern_packs=["default", "custom"])
    sanitizer = Sanitizer(config)
    
    combined_tests = [
        ("Mixed PII", "Employee EMP123456 email john@company.com works on PROJ-2024-001"),
        ("International", "Contact María García at maria@empresa.es about customer CUST-ESP-789"),
        ("Full Example", "Employee EMP555666 (john.doe@company.com, DNI: 12345678Z) working on PROJ-2024-003"),
    ]
    
    for desc, text in combined_tests:
        print(f"\n{desc}:")
        print(f"  Input:  {text}")
        try:
            masked, mask_map = sanitizer.sanitize(text)
            print(f"  Output: {masked}")
            if mask_map:
                print(f"    Found {len(mask_map)} PII entities:")
                for placeholder, original in mask_map.items():
                    entity_type = placeholder.split('_')[1] if '_' in placeholder else placeholder
                    print(f"      {entity_type}: {original}")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Demo 4: Context keyword validation
    print(f"\n\n🎯 Demo 4: Context Keyword Validation")
    print("-" * 40)
    print("Pattern packs include context keywords to reduce false positives:")
    
    context_tests = [
        ("With Context", "Please provide your DNI: 12345678Z for verification"),
        ("Without Context", "Random number 12345678Z has no context"),
        ("Credit Card Context", "Payment card number: 4111-1111-1111-1111"),
        ("Random Numbers", "Reference code 4111-1111-1111-1111 unrelated"),
    ]
    
    for desc, text in context_tests:
        print(f"\n{desc}:")
        print(f"  Input:  {text}")
        try:
            masked, mask_map = sanitizer.sanitize(text)
            print(f"  Output: {masked}")
            if mask_map:
                print(f"    ✅ PII detected (context matched)")
            else:
                print(f"    ❌ No PII detected (context not matched)")
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"\n" + "=" * 60)
    print("✅ Pattern Pack Demo completed!")
    print("\n📋 Summary:")
    print("• Default pack: Universal + country-specific patterns")
    print("• Custom packs: Organization-specific patterns") 
    print("• Combined packs: Best of both worlds")
    print("• Context validation: Reduces false positives")
    print("• YAML format: Easy to create and maintain")
    
    print(f"\n📁 Pattern Pack Files:")
    print("• patterns/default.yaml - Built-in patterns")
    print("• patterns/custom.yaml - Example custom patterns")
    print("• Create your own: patterns/yourorg.yaml")
    
    print(f"\n🔧 Usage:")
    print("• Python: Config(pattern_packs=['default', 'custom'])")
    print("• CLI: --pattern-packs custom")
    print("• API: Load via configuration")

if __name__ == "__main__":
    main()