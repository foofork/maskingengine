# Pattern Pack Sourcing Guide

This guide helps you find, create, and source regex pattern packs for industry-specific PII detection with MaskingEngine.

## Table of Contents

1. [Overview](#overview)
2. [Industry Pattern Sources](#industry-pattern-sources)
3. [Community Resources](#community-resources)
4. [Creating Custom Patterns](#creating-custom-patterns)
5. [Pattern Pack Validation](#pattern-pack-validation)
6. [Contributing Back](#contributing-back)

---

## Overview

MaskingEngine comes with comprehensive default patterns for common PII types, but you may need specialized patterns for:

- **Industry-specific identifiers** (medical record numbers, financial account IDs)
- **Regional variations** (country-specific phone numbers, postal codes) 
- **Organizational formats** (employee IDs, custom reference numbers)
- **Compliance requirements** (HIPAA, GDPR, SOX-specific data types)

Industry-specific patterns can be easily added as custom pattern packs using the template format.

---

## Industry Pattern Sources

### Healthcare (HIPAA) - Example Custom Pattern Pack

Healthcare-specific patterns are now included in the default pattern pack. If you need additional healthcare patterns, create a custom pattern pack:

```yaml
# custom.yaml - Example healthcare patterns
name: "custom"
description: "Custom healthcare patterns for your organization"
version: "1.0.0"

patterns:
  # Example: Additional medical patterns not in default
  - name: HOSPITAL_CODE
    description: "Hospital-specific codes"
    tier: 1
    language: "universal"
    patterns:
      - '\bHOSP-[A-Z]{2,4}-\d{4,6}\b'
    examples:
      - "1234567890"

  - label: "DEA_NUMBER"
    pattern: '\b[A-Z]{2}[0-9]{7}\b'
    description: "DEA registration numbers"
    examples:
      - "AB1234567"
```

#### Healthcare Data Sources
- **CMS Data Elements**: [CMS.gov Data Element Library](https://www.cms.gov/data-research)
- **HL7 Standards**: [HL7.org](https://www.hl7.org/) for healthcare data formats
- **HIPAA Safe Harbor**: [HHS.gov HIPAA Guidelines](https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/)

### Finance (SOX/PCI-DSS) - Example Custom Pattern Pack

Financial patterns like credit cards and SSNs are included in the default pattern pack. For additional financial patterns:

```yaml
# custom.yaml - Example financial patterns
name: "custom"
description: "Custom financial patterns for your organization"
version: "1.0.0"

patterns:
  # Example: Additional financial patterns not in default
  - name: ROUTING_NUMBER
    description: "US bank routing numbers (ABA)"
    tier: 1
    language: "universal"
    patterns:
      - '\b[0-9]{9}\b'

  - name: SWIFT_CODE
    description: "SWIFT/BIC codes"
    tier: 1
    language: "universal"
    patterns:
      - '\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?\b'
```

#### Financial Data Sources
- **SWIFT Standards**: [SWIFT.com](https://www.swift.com/) for international banking codes
- **SEC Data**: [SEC.gov EDGAR](https://www.sec.gov/edgar) for financial reporting standards
- **PCI Security Standards**: [PCISecurityStandards.org](https://www.pcisecuritystandards.org/)

### Legal

#### Legal Document Patterns
```yaml
# legal.yaml
meta:
  name: "legal"
  description: "Legal industry patterns for document processing"
  domain: "legal"
  lang: ["en"]

patterns:
  - label: "CASE_NUMBER"
    pattern: '\b[0-9]{2}-[A-Z]{2,4}-[0-9]{4,6}\b'
    description: "Court case numbers"
    examples:
      - "22-CV-123456"
      - "21-CR-98765"

  - label: "BAR_NUMBER"
    pattern: '\b(BAR|#)[0-9]{6,8}\b'
    description: "Attorney bar numbers"
    examples:
      - "BAR123456"
      - "#12345678"

  - label: "DOCKET_NUMBER"
    pattern: '\bDocket\s+No\.\s+[0-9]{2}-[0-9]{4,6}\b'
    description: "Legal docket numbers"
    examples:
      - "Docket No. 22-12345"
```

### Government

#### Government ID Patterns
```yaml
# government.yaml
meta:
  name: "government"
  description: "Government and public sector ID patterns"
  domain: "government"
  lang: ["en"]

patterns:
  - label: "PASSPORT_NUMBER"
    pattern: '\b[A-Z0-9]{6,9}\b'
    description: "US passport numbers"
    examples:
      - "123456789"

  - label: "VISA_NUMBER"
    pattern: '\b[0-9]{8,12}\b'
    description: "Visa control numbers"
    examples:
      - "123456789012"

  - label: "TSA_PRECHECK"
    pattern: '\b[0-9]{8,10}\b'
    description: "TSA PreCheck known traveler numbers"
    examples:
      - "1234567890"
```

---

## Community Resources

### Open Source Collections

#### General PII Patterns
- **CommonRegex**: [GitHub - CommonRegex](https://github.com/madisonmay/CommonRegex)
- **Regex Library**: [RegexLib.com](http://regexlib.com/)
- **Awesome Regex**: [GitHub - Awesome Regex](https://github.com/aloisdg/awesome-regex)

#### Industry-Specific
- **Medical RegEx**: [Healthcare Data Patterns](https://github.com/search?q=medical+regex)
- **Financial RegEx**: [Banking Pattern Collections](https://github.com/search?q=financial+regex)
- **Government ID RegEx**: [Government ID Patterns](https://github.com/search?q=government+id+regex)

### Commercial Sources

#### Pattern Databases
- **Sensitive Data Discovery Tools**: Many commercial tools publish pattern libraries
- **Compliance Consultants**: Industry-specific consulting firms often maintain pattern collections
- **Security Vendors**: Data loss prevention (DLP) vendors publish detection patterns

### Academic Sources

#### Research Papers
- **PII Detection Research**: Academic papers on automated PII detection
- **Privacy Engineering**: Research on privacy-preserving technologies
- **Regulatory Compliance**: Studies on industry-specific compliance requirements

---

## Creating Custom Patterns

### Pattern Development Process

1. **Identify Requirements**
   ```bash
   # Research the data format
   - What is the exact format specification?
   - Are there checksums or validation rules?
   - What are the valid ranges or character sets?
   ```

2. **Collect Examples**
   ```bash
   # Gather real-world examples (anonymized)
   - Valid examples
   - Invalid examples (for testing)
   - Edge cases and variations
   ```

3. **Develop Patterns**
   ```bash
   # Start simple, then refine
   - Basic pattern matching the format
   - Add validation rules
   - Handle edge cases
   - Optimize for performance
   ```

4. **Test Thoroughly**
   ```bash
   # Validate pattern performance
   - Test with known examples
   - Check for false positives
   - Verify performance on large text
   ```

### Pattern Development Tools

#### Online Regex Testers
- **RegEx101**: [regex101.com](https://regex101.com/) - Interactive regex tester
- **RegExr**: [regexr.com](https://regexr.com/) - Learn and test regex patterns
- **RegexPal**: [regexpal.com](https://www.regexpal.com/) - Simple online tester

#### Development Environment
```python
# Test patterns programmatically
import re

def test_pattern(pattern: str, test_cases: dict):
    """Test a regex pattern against known cases."""
    compiled = re.compile(pattern, re.IGNORECASE)
    
    results = {
        'true_positives': 0,
        'false_positives': 0,
        'true_negatives': 0,
        'false_negatives': 0
    }
    
    for text, should_match in test_cases.items():
        matches = bool(compiled.search(text))
        
        if matches and should_match:
            results['true_positives'] += 1
        elif matches and not should_match:
            results['false_positives'] += 1
        elif not matches and not should_match:
            results['true_negatives'] += 1
        else:  # not matches and should_match
            results['false_negatives'] += 1
    
    return results

# Example usage
ssn_pattern = r'\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b'
test_cases = {
    "123-45-6789": True,    # Valid SSN
    "000-00-0000": True,    # Valid format (even if invalid SSN)
    "123456789": False,     # No hyphens
    "123-45-67890": False,  # Too many digits
    "abc-de-fghi": False,   # Letters instead of numbers
}

results = test_pattern(ssn_pattern, test_cases)
print(f"Accuracy: {(results['true_positives'] + results['true_negatives']) / sum(results.values())}")
```

### Industry-Specific Pattern Examples

#### Education
```yaml
# education.yaml
patterns:
  - label: "STUDENT_ID"
    pattern: '\b(STU|ID)[0-9]{6,9}\b'
    description: "Student identification numbers"
    
  - label: "FERPA_RECORD"
    pattern: '\b[0-9]{4}-[0-9]{6}\b'
    description: "FERPA protected educational records"
```

#### Retail
```yaml
# retail.yaml
patterns:
  - label: "LOYALTY_CARD"
    pattern: '\b[0-9]{4}\s[0-9]{4}\s[0-9]{4}\s[0-9]{4}\b'
    description: "Customer loyalty card numbers"
    
  - label: "SKU"
    pattern: '\bSKU[A-Z0-9]{6,12}\b'
    description: "Stock keeping unit identifiers"
```

#### Manufacturing
```yaml
# manufacturing.yaml
patterns:
  - label: "SERIAL_NUMBER"
    pattern: '\bSN[A-Z0-9]{8,15}\b'
    description: "Product serial numbers"
    
  - label: "LOT_NUMBER"
    pattern: '\bLOT[0-9]{8}\b'
    description: "Manufacturing lot numbers"
```

---

## Pattern Pack Validation

### Validation Checklist

1. **Format Validation**
   ```bash
   # Use MaskingEngine validation
   maskingengine validate-config custom_pack.yaml
   ```

2. **Performance Testing**
   ```python
   # Test pattern performance
   import time
   import re
   
   def benchmark_pattern(pattern: str, text: str, iterations: int = 1000):
       compiled = re.compile(pattern)
       start_time = time.time()
       
       for _ in range(iterations):
           compiled.findall(text)
       
       end_time = time.time()
       return (end_time - start_time) / iterations
   ```

3. **Accuracy Testing**
   ```python
   # Test with sample data
   def validate_accuracy(pattern_pack: str):
       from maskingengine import Sanitizer, Config
       
       config = Config(pattern_packs=[pattern_pack])
       sanitizer = Sanitizer(config)
       
       # Test with known examples
       test_cases = load_test_cases(pattern_pack)
       
       for case in test_cases:
           masked, _ = sanitizer.sanitize(case['input'])
           # Verify expected masking occurred
   ```

### Common Validation Issues

#### Performance Problems
```yaml
# ❌ Problematic pattern (catastrophic backtracking)
- label: "BAD_PATTERN"
  pattern: '(.*)*email.*'  # Dangerous nested quantifiers

# ✅ Better pattern
- label: "GOOD_PATTERN"
  pattern: '\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
```

#### False Positives
```yaml
# ❌ Too broad (matches legitimate numbers)
- label: "TOO_BROAD"
  pattern: '[0-9]+'  # Matches any number

# ✅ More specific
- label: "SPECIFIC"
  pattern: '\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b'  # Exact SSN format
```

#### Internationalization Issues
```yaml
# ❌ US-only phone pattern
- label: "US_ONLY"
  pattern: '\([0-9]{3}\) [0-9]{3}-[0-9]{4}'

# ✅ International-aware
- label: "INTERNATIONAL_PHONE"
  pattern: '(\+[1-9]\d{1,14})|(\([0-9]{3}\) [0-9]{3}-[0-9]{4})'
```

---

## Contributing Back

### Sharing Pattern Packs

#### Community Contributions
1. **Fork the Repository**: Create your own pattern pack
2. **Follow Conventions**: Use the standard format and naming
3. **Include Tests**: Provide test cases and validation
4. **Document Usage**: Clear descriptions and examples
5. **Submit Pull Request**: Contribute back to the community

#### Pattern Pack Standards
```yaml
# Standard format for community packs
meta:
  name: "industry_region"  # e.g., "healthcare_us"
  description: "Clear description of what this pack detects"
  version: "1.0.0"
  author: "Your Name <email@example.com>"
  license: "MIT"  # Or appropriate license
  lang: ["en", "es"]  # Languages supported
  domain: "healthcare"  # Industry domain
  compliance: ["HIPAA", "HITECH"]  # Relevant regulations

patterns:
  # Well-documented patterns with examples
```

#### Quality Guidelines
- **Accuracy**: Patterns should have >95% precision
- **Performance**: Should process 1MB of text in <100ms
- **Documentation**: Clear descriptions and examples
- **Testing**: Include comprehensive test cases
- **Compliance**: Note relevant regulatory frameworks

### Industry Collaboration

#### Building Industry-Specific Collections
1. **Healthcare Consortium**: Collaborate on HIPAA-compliant patterns
2. **Financial Services**: Work with banks on PCI-DSS patterns
3. **Government**: Partner with agencies on classification patterns
4. **Legal**: Collaborate with law firms on document patterns

#### Best Practices for Collaboration
- **Anonymize Examples**: Never include real PII in pattern examples
- **Document Sources**: Cite official specifications and standards
- **Version Control**: Use semantic versioning for pattern updates
- **Testing**: Provide comprehensive test suites
- **Licensing**: Use permissive licenses for maximum adoption

---

## Resources and References

### Official Standards
- **ISO 27001**: Information security management
- **NIST Privacy Framework**: Privacy risk management
- **GDPR**: EU General Data Protection Regulation
- **CCPA**: California Consumer Privacy Act

### Industry Guidelines
- **HIPAA**: Healthcare privacy standards
- **PCI-DSS**: Payment card industry standards
- **SOX**: Financial reporting requirements
- **FERPA**: Educational privacy standards

### Technical Resources
- **Regular Expression Libraries**: Language-specific regex documentation
- **Unicode Standards**: For international character support
- **Privacy Engineering**: Technical privacy protection methods
- **Data Classification**: Standards for data sensitivity levels

---

Remember: Always validate patterns with legal and compliance teams before deploying in production environments handling sensitive data.