# Pattern Packs Guide

Pattern packs are YAML-based configuration files that define the PII detection rules used by MaskingEngine. They provide a flexible, extensible way to customize PII detection for different domains, languages, and organizational needs.

## Overview

MaskingEngine uses a pure YAML-based pattern system that supports:
- **Universal patterns** - Language-agnostic rules (emails, credit cards, IPs)
- **Language-specific patterns** - Localized rules (French phone numbers, German tax IDs)
- **Custom organizational patterns** - Company-specific PII (employee IDs, internal codes)
- **Tiered priority system** - Control which patterns take precedence
- **Multiple pattern variations** - Support different formats for the same PII type

## Pattern Pack Structure

### Basic YAML Format

```yaml
# Pattern pack metadata
name: "my_custom_pack"
description: "Custom patterns for my organization"
version: "1.0.0"

# Pattern definitions
patterns:
  - name: PATTERN_NAME
    description: "Human-readable description"
    tier: 1                    # Priority tier (1 = highest)
    language: "universal"      # "universal", "en", "fr", "de", etc.
    country: "US"             # Optional country code
    patterns:                 # List of regex patterns
      - 'regex_pattern_1'
      - 'regex_pattern_2'
```

### Field Definitions

**Metadata Fields:**
- `name` (string): Unique identifier for the pattern pack
- `description` (string): Human-readable description
- `version` (string): Semantic version for the pack

**Pattern Fields:**
- `name` (string): PII type identifier (uppercase, underscore-separated)
- `description` (string): Description of what this pattern detects
- `tier` (integer): Priority tier (1 = highest priority, 3 = lowest)
- `language` (string): Language code ("universal", "en", "fr", "de", etc.)
- `country` (string, optional): Country code for region-specific patterns
- `patterns` (array): List of regex patterns for detection

---

## Default Pattern Pack

MaskingEngine ships with a comprehensive default pattern pack (`default.yaml`) that includes:

### Universal Patterns (Tier 1)

**EMAIL** - Email addresses
```yaml
- name: EMAIL
  description: "Universal email address detection"
  tier: 1
  language: "universal"
  patterns:
    - '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
```

**CREDIT_CARD_NUMBER** - Credit card numbers
```yaml
- name: CREDIT_CARD_NUMBER
  description: "Enhanced credit card detection (Visa, Mastercard, Amex, etc.)"
  tier: 1
  language: "universal"
  patterns:
    - '\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b'
```

**US_SSN** - U.S. Social Security Numbers
```yaml
- name: US_SSN
  description: "U.S. Social Security Numbers with flexible formatting"
  tier: 1
  language: "universal"
  country: "US"
  patterns:
    - '\b\d{3}[-.]?\d{2}[-.]?\d{4}\b'
    - '\b\d{9}\b'
```

**IPV4** - IPv4 addresses
```yaml
- name: IPV4
  description: "IPv4 address detection"
  tier: 1
  language: "universal"
  patterns:
    - '\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
```

### Phone Number Patterns (Tier 2)

**US_PHONE** - U.S. phone numbers
```yaml
- name: US_PHONE
  description: "U.S. phone numbers with various formatting"
  tier: 2
  language: "en"
  country: "US"
  patterns:
    - '\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
    - '\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
```

**INTERNATIONAL_PHONE** - International formats
```yaml
- name: INTERNATIONAL_PHONE
  description: "International phone numbers with country codes"
  tier: 2
  language: "universal"
  patterns:
    - '\+\d{1,3}[\s.-]?\d{1,14}'
    - '\b00\d{1,3}[\s.-]?\d{1,14}'
```

### Language-Specific Patterns (Tier 2)

**FR_PHONE_NUMBER** - French phone numbers
```yaml
- name: FR_PHONE_NUMBER
  description: "French phone numbers"
  tier: 2
  language: "fr"
  country: "FR"
  patterns:
    - '\b0[1-9](?:[\s.-]?\d{2}){4}\b'
    - '\+33[\s.-]?[1-9](?:[\s.-]?\d{2}){4}'
```

**GERMAN_TAX_ID** - German tax identification
```yaml
- name: GERMAN_TAX_ID
  description: "German tax identification number"
  tier: 2
  language: "de"
  country: "DE"
  patterns:
    - '\b\d{11}\b'
```

---

## Creating Custom Pattern Packs

### Step 1: Create YAML File

Create a new YAML file in your patterns directory:

```yaml
# File: patterns/enterprise.yaml
name: "enterprise"
description: "Enterprise-specific PII patterns"
version: "1.0.0"

patterns:
  # Employee identification
  - name: EMPLOYEE_ID
    description: "Employee IDs in format EMP123456"
    tier: 1
    language: "universal"
    patterns:
      - '\bEMP\d{6}\b'
      - '\b[Ee]mployee[\s#:-]?\d{6}\b'

  # Internal project codes
  - name: PROJECT_CODE
    description: "Project codes like PROJ-2024-001"
    tier: 1
    language: "universal"
    patterns:
      - '\bPROJ-\d{4}-\d{3}\b'
      - '\bProject[\s#:-]?[A-Z]{2,4}-\d{3,4}\b'

  # API keys and secrets
  - name: API_KEY
    description: "API keys and tokens"
    tier: 1
    language: "universal"
    patterns:
      - '\bsk-[a-zA-Z0-9]{32,}\b'        # OpenAI style
      - '\bapi[_-]?key[_-]?[a-zA-Z0-9]{32,}\b'
      - '\btoken[_-]?[a-zA-Z0-9]{40,}\b'

  # Customer identifiers
  - name: CUSTOMER_ID
    description: "Customer IDs in format CUST-ABC-123"
    tier: 2
    language: "universal"
    patterns:
      - '\bCUST-[A-Z]{3}-\d{3}\b'
      - '\bCustomer[\s#:-]?[A-Z0-9]{6,12}\b'
```

### Step 2: Use Custom Pack

**Python SDK:**
```python
from maskingengine import Sanitizer, Config

# Use custom pattern pack
config = Config(pattern_packs=["enterprise"])
sanitizer = Sanitizer(config)

content = "Employee EMP123456 worked on PROJ-2024-001"
masked, mask_map = sanitizer.sanitize(content)
# Result: "Employee <<EMPLOYEE_ID_...>> worked on <<PROJECT_CODE_...>>"
```

**CLI:**
```bash
# Use custom pattern pack
maskingengine mask input.txt --pattern-packs enterprise -o output.txt

# Use multiple packs
maskingengine mask input.txt --pattern-packs default enterprise -o output.txt
```

**REST API:**
```bash
curl -X POST "http://localhost:8000/sanitize" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Employee EMP123456 has API key sk-abc123...",
    "pattern_packs": ["enterprise"]
  }'
```

---

## Advanced Pattern Techniques

### Multiple Pattern Variations

Support different formats for the same PII type:

```yaml
- name: PHONE_NUMBER
  description: "Phone numbers with multiple format support"
  tier: 2
  language: "universal"
  patterns:
    - '\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'           # 123-456-7890
    - '\(\d{3}\)\s?\d{3}[-.]?\d{4}'             # (123) 456-7890
    - '\+\d{1,3}[\s.-]?\d{1,14}'                # +1 123 456 7890
    - '\b\d{10}\b'                              # 1234567890
```

### Language-Specific Patterns

Create patterns for specific languages and regions:

```yaml
# Spanish patterns
- name: SPANISH_DNI
  description: "Spanish national ID (DNI)"
  tier: 1
  language: "es"
  country: "ES"
  patterns:
    - '\b\d{8}[A-Z]\b'

# French patterns  
- name: FRENCH_SIRET
  description: "French SIRET business identifier"
  tier: 1
  language: "fr"
  country: "FR"
  patterns:
    - '\b\d{14}\b'

# German patterns
- name: GERMAN_IBAN
  description: "German IBAN bank account"
  tier: 1
  language: "de"
  country: "DE"
  patterns:
    - '\bDE\d{20}\b'
```

### Tiered Priority System

Use tiers to control pattern precedence:

```yaml
# Tier 1: Critical PII (always detected)
- name: SSN
  tier: 1
  # ...

# Tier 2: Important PII (detected unless disabled)
- name: PHONE
  tier: 2  
  # ...

# Tier 3: Optional PII (only in comprehensive mode)
- name: INTERNAL_CODE
  tier: 3
  # ...
```

### Domain-Specific Patterns

Create patterns for specific industries:

```yaml
# Healthcare patterns
- name: MEDICAL_RECORD_NUMBER
  description: "Medical record numbers"
  tier: 1
  language: "universal"
  patterns:
    - '\bMRN[\s#:-]?\d{6,10}\b'
    - '\bMedical[\s_]?Record[\s#:-]?\d{6,10}\b'

# Financial patterns
- name: ACCOUNT_NUMBER
  description: "Bank account numbers"
  tier: 1
  language: "universal"
  patterns:
    - '\bACC[\s#:-]?\d{8,12}\b'
    - '\bAccount[\s#:-]?\d{8,12}\b'

# Legal patterns
- name: CASE_NUMBER
  description: "Legal case numbers"
  tier: 2
  language: "universal"
  patterns:
    - '\bCase[\s#:-]?\d{4}-\d{6}\b'
    - '\b\d{4}[A-Z]{2}\d{6}\b'
```

---

## Pattern Pack Management

### Loading Multiple Packs

Combine multiple pattern packs for comprehensive coverage:

```python
# Load default + custom patterns
config = Config(pattern_packs=["default", "enterprise", "healthcare"])
sanitizer = Sanitizer(config)
```

### Pattern Pack Discovery

MaskingEngine searches for pattern packs in:
1. Package installation directory: `maskingengine/patterns/`
2. Current working directory: `./patterns/`
3. Custom directory via configuration

### Pattern Compilation

Patterns are compiled at runtime with error handling:
- Invalid regex patterns are skipped with warnings
- Compilation errors don't break the entire pack
- Valid patterns continue to work normally

---

## Best Practices

### Pattern Design

**DO:**
- Use specific, targeted patterns to avoid false positives
- Include word boundaries (`\b`) to prevent partial matches
- Test patterns with diverse sample data
- Use descriptive names and comments
- Include multiple format variations

**DON'T:**
- Create overly broad patterns that match common text
- Use patterns without proper escaping
- Forget to test edge cases and boundary conditions
- Create patterns that overlap significantly
- Use capture groups unless necessary

### Performance Optimization

**Fast Patterns:**
```yaml
# Good: Specific and efficient
- '\b\d{3}-\d{2}-\d{4}\b'         # SSN format

# Good: Uses word boundaries
- '\bEMP\d{6}\b'                  # Employee ID
```

**Slow Patterns:**
```yaml
# Avoid: Too broad and slow
- '.*@.*\..*'                     # Overly broad email

# Avoid: Complex backtracking
- '([a-zA-Z0-9._%+-]+)*@.*'       # Catastrophic backtracking
```

### Testing Custom Patterns

Test your patterns thoroughly:

```python
import re

# Test pattern compilation
pattern = r'\bEMP\d{6}\b'
try:
    compiled = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
    print("Pattern compiles successfully")
except re.error as e:
    print(f"Pattern error: {e}")

# Test pattern matching
test_cases = [
    "Employee EMP123456 is here",      # Should match
    "EMP123456",                       # Should match  
    "EMP12345",                        # Should not match (5 digits)
    "XEMP123456",                      # Should not match (no boundary)
]

for test in test_cases:
    matches = compiled.findall(test)
    print(f"'{test}' -> {matches}")
```

### Validation and Quality Control

Validate your pattern packs:

```bash
# Test pattern pack loading
python -c "
from maskingengine import Config
try:
    config = Config(pattern_packs=['your_pack'])
    print('Pattern pack loaded successfully')
except Exception as e:
    print(f'Error: {e}')
"

# Test detection with sample data
echo 'EMP123456 worked on PROJ-2024-001' | \
  maskingengine mask --stdin --pattern-packs your_pack
```

---

## Example Pattern Packs

### Healthcare Pattern Pack

```yaml
name: "healthcare"
description: "Healthcare-specific PII patterns"
version: "1.0.0"

patterns:
  - name: MEDICAL_RECORD_NUMBER
    description: "Medical record numbers"
    tier: 1
    language: "universal"
    patterns:
      - '\bMRN[\s#:-]?\d{6,10}\b'
      - '\bMR[\s#:-]?\d{6,10}\b'

  - name: PATIENT_ID
    description: "Patient identification numbers"
    tier: 1
    language: "universal"
    patterns:
      - '\bPT[\s#:-]?\d{6,10}\b'
      - '\bPatient[\s#:-]?\d{6,10}\b'

  - name: DEA_NUMBER
    description: "DEA prescription numbers"
    tier: 1
    language: "universal"
    country: "US"
    patterns:
      - '\b[A-Z]{2}\d{7}\b'
```

### Financial Pattern Pack

```yaml
name: "financial"
description: "Financial services PII patterns"
version: "1.0.0"

patterns:
  - name: ACCOUNT_NUMBER
    description: "Bank account numbers"
    tier: 1
    language: "universal"
    patterns:
      - '\b\d{8,17}\b'
      - '\bACC[\s#:-]?\d{8,12}\b'

  - name: ROUTING_NUMBER
    description: "U.S. bank routing numbers"
    tier: 1
    language: "universal"
    country: "US"
    patterns:
      - '\b\d{9}\b(?=.*routing)'
      - '\bRT[\s#:-]?\d{9}\b'

  - name: SWIFT_CODE
    description: "SWIFT/BIC codes"
    tier: 1
    language: "universal"
    patterns:
      - '\b[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?\b'
```

### Technology Pattern Pack

```yaml
name: "technology"
description: "Technology and API-related PII patterns"
version: "1.0.0"

patterns:
  - name: API_KEY
    description: "Various API key formats"
    tier: 1
    language: "universal"
    patterns:
      - '\bsk-[a-zA-Z0-9]{32,}\b'           # OpenAI
      - '\bxoxb-[a-zA-Z0-9-]{50,}\b'        # Slack
      - '\bghp_[a-zA-Z0-9]{36}\b'           # GitHub
      - '\bAKIA[A-Z0-9]{16}\b'              # AWS

  - name: JWT_TOKEN
    description: "JSON Web Tokens"
    tier: 1
    language: "universal"
    patterns:
      - '\beyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\b'

  - name: DATABASE_URL
    description: "Database connection strings"
    tier: 1
    language: "universal"
    patterns:
      - '\b(postgresql|mysql|mongodb)://[^\s]+\b'
      - '\bServer=[^;]+;Database=[^;]+;User[^;]+;Password=[^;]+\b'
```

---

## Troubleshooting

### Common Issues

**Pattern not matching:**
- Check word boundaries (`\b`)
- Verify regex escaping
- Test with simple test cases
- Check tier and language settings

**Performance issues:**
- Avoid complex patterns with backtracking
- Use specific patterns instead of broad ones
- Test with large datasets
- Profile pattern compilation time

**Loading errors:**
- Validate YAML syntax
- Check file permissions
- Verify pattern pack location
- Review error messages for specific issues

### Debug Mode

Enable verbose logging to debug pattern issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from maskingengine import Sanitizer, Config
config = Config(pattern_packs=["debug_pack"])
sanitizer = Sanitizer(config)
```

This will show detailed information about:
- Pattern pack loading
- Pattern compilation
- Match attempts and results
- Performance metrics

---

This comprehensive guide should help you create effective, maintainable pattern packs for your specific PII detection needs. Remember to test thoroughly and follow the best practices for optimal performance and accuracy.