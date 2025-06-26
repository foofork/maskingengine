#!/usr/bin/env python3
"""
MaskingEngine Multilingual NER Demonstration

This script demonstrates the multilingual PII detection capabilities
using the yonigo/distilbert-base-multilingual-cased-pii model.
"""

from maskingengine import Sanitizer


def main():
    print("🌍 MaskingEngine - Multilingual PII Detection Demo")
    print("=" * 60)

    # Initialize sanitizer with NER enabled
    sanitizer = Sanitizer()

    # Test cases in different languages
    test_cases = [
        ("English", "Contact john.smith@company.com or call +1-555-123-4567"),
        ("Spanish", "Contacta a maria.garcia@empresa.es para más información"),
        ("French", "Appelez le +33-1-23-45-67-89 ou écrivez à jean@societe.fr"),
        ("German", "Kontaktieren Sie uns unter hans@firma.de oder +49-30-12345678"),
        ("Portuguese", "Contate joão.silva@empresa.com.br ou ligue para obter ajuda"),
        ("Mixed", "Email: user@test.com, Téléphone: +33-1-23-45-67-89, SSN: 123-45-6789"),
    ]

    for language, text in test_cases:
        print(f"\n📝 {language}:")
        print(f"   Input:  {text}")

        try:
            masked, mask_map = sanitizer.sanitize(text)
            print(f"   Output: {masked}")

            if mask_map:
                print(f"   Found:  {len(mask_map)} PII entities")
                for placeholder, original in mask_map.items():
                    entity_type = placeholder.split("_")[1]
                    print(f"     • {entity_type}: {original}")
            else:
                print("   Found:  No PII detected")

        except Exception as e:
            print(f"   Error:  {e}")

    print(f"\n✅ Demo completed!")
    print(f"\n💡 NER Model: yonigo/distilbert-base-multilingual-cased-pii")
    print(f"🔧 Detected Types: EMAIL, TEL (phone), SOCIALNUMBER (SSN)")
    print(f"🚀 Also supports: Regex-based detection for credit cards, IPs, etc.")


if __name__ == "__main__":
    main()
