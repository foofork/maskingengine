#!/bin/bash
# MaskingEngine CLI Examples

echo "🚀 MaskingEngine CLI Examples"
echo "============================"
echo

# Create sample data
echo "Creating sample files..."
cat > sample.txt << EOF
Contact Information:
Name: John Doe
Email: john.doe@example.com
Phone: 555-123-4567
SSN: 123-45-6789
Credit Card: 4532-1234-5678-9012
IP Address: 192.168.1.100
EOF

cat > sample.json << EOF
{
  "customer": {
    "name": "Jane Smith",
    "email": "jane.smith@company.com",
    "phone": "+1-555-987-6543",
    "address": "123 Main St, New York, NY"
  },
  "order": {
    "id": "ORD-12345",
    "total": 99.99,
    "card_last_four": "4242"
  }
}
EOF

echo "✅ Sample files created"
echo

# Example 1: Basic text masking
echo "Example 1: Basic Text Masking"
echo "-----------------------------"
echo "Command: ./maskingengine-cli mask sample.txt -o masked.txt -m masks.json"
./maskingengine-cli mask sample.txt -o masked.txt -m masks.json
echo
cat masked.txt
echo

# Example 2: JSON masking
echo "Example 2: JSON Masking"
echo "-----------------------"
echo "Command: ./maskingengine-cli mask sample.json -f json -o masked.json -m masks_json.json"
./maskingengine-cli mask sample.json -f json -o masked.json -m masks_json.json
echo
cat masked.json
echo

# Example 3: Pipe usage
echo "Example 3: Using Pipes"
echo "----------------------"
echo "Command: echo 'Call me at 555-1234' | ./maskingengine-cli mask --stdin"
echo "Call me at 555-1234" | ./maskingengine-cli mask --stdin
echo

# Example 4: Custom configuration
echo "Example 4: Custom Configuration"
echo "-------------------------------"
echo "Command: ./maskingengine-cli mask sample.txt --placeholder-prefix 'HIDDEN_' --min-confidence 0.9"
./maskingengine-cli mask sample.txt --placeholder-prefix "HIDDEN_" --min-confidence 0.9
echo

# Example 5: Whitelist usage
echo "Example 5: Using Whitelist"
echo "--------------------------"
echo "Command: ./maskingengine-cli mask sample.txt --whitelist 'John Doe' --whitelist 'example.com'"
./maskingengine-cli mask sample.txt --whitelist "John Doe" --whitelist "example.com"
echo

# Example 6: Disable specific detectors
echo "Example 6: Disable NER (regex only)"
echo "-----------------------------------"
echo "Command: ./maskingengine-cli mask sample.txt --no-ner"
./maskingengine-cli mask sample.txt --no-ner
echo

# Example 7: Unmask (rehydrate)
echo "Example 7: Unmask (Rehydrate)"
echo "-----------------------------"
echo "Command: ./maskingengine-cli unmask masked.txt -m masks.json -o restored.txt"
./maskingengine-cli unmask masked.txt -m masks.json -o restored.txt
echo
echo "Original vs Restored:"
diff -u sample.txt restored.txt && echo "✅ Files match - successful round trip!" || echo "❌ Files differ"
echo

# Example 8: Test command
echo "Example 8: Test Command"
echo "-----------------------"
echo "Command: ./maskingengine-cli test"
./maskingengine-cli test
echo

# Cleanup
echo "Cleaning up sample files..."
rm -f sample.txt sample.json masked.txt masked.json masks.json masks_json.json restored.txt

echo "✅ Examples completed!"