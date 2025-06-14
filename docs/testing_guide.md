# Phase 4: Testing Strategy and TDD Anchors

## 1. Test-Driven Development Strategy

### 1.1 TDD Workflow
1. **Red Phase**: Write failing tests for each requirement
2. **Green Phase**: Implement minimal code to pass tests
3. **Refactor Phase**: Optimize while maintaining test coverage

### 1.2 Test Categories
- **Unit Tests**: Individual component validation
- **Integration Tests**: Module interaction testing
- **Performance Tests**: Latency and throughput validation
- **Edge Case Tests**: Boundary condition handling
- **Regression Tests**: Prevent feature breakage

## 2. Unit Test Specifications

### 2.1 Regex Detector Tests
```python
# tests/test_regex_detector.py
import pytest
from maskingengine.detectors import RegexDetector
from maskingengine.core.types import PIIType

class TestRegexDetector:
    def test_email_detection_basic(self):
        """Test basic email pattern detection"""
        detector = RegexDetector()
        text = "Contact me at john.doe@example.com"
        detections = detector.detect(text)
        
        assert len(detections) == 1
        assert detections[0].type == PIIType.EMAIL
        assert detections[0].text == "john.doe@example.com"
        assert detections[0].start == 14
        assert detections[0].end == 34
    
    def test_email_detection_edge_cases(self):
        """Test email edge cases"""
        test_cases = [
            ("user+tag@example.co.uk", True),
            ("name@sub.domain.com", True),
            ("test_email@company-name.org", True),
            ("invalid@.com", False),
            ("@example.com", False),
            ("user@", False)
        ]
        
        detector = RegexDetector()
        for email, should_detect in test_cases:
            detections = detector.detect(email)
            assert bool(detections) == should_detect
    
    def test_phone_number_us_formats(self):
        """Test US phone number formats"""
        test_cases = [
            "(555) 123-4567",
            "555-123-4567",
            "555.123.4567",
            "+1 555 123 4567",
            "5551234567"
        ]
        
        detector = RegexDetector()
        for phone in test_cases:
            detections = detector.detect(f"Call me at {phone}")
            assert len(detections) == 1
            assert detections[0].type == PIIType.PHONE
    
    def test_ssn_detection(self):
        """Test SSN pattern detection"""
        valid_ssns = ["123-45-6789", "987-65-4321"]
        invalid_ssns = ["123456789", "12-345-6789", "1234-56-789"]
        
        detector = RegexDetector()
        for ssn in valid_ssns:
            detections = detector.detect(ssn)
            assert len(detections) == 1
            assert detections[0].type == PIIType.SSN
        
        for ssn in invalid_ssns:
            detections = detector.detect(ssn)
            assert len(detections) == 0
    
    def test_credit_card_with_luhn(self):
        """Test credit card detection with Luhn validation"""
        valid_cards = [
            "4532015112830366",  # Valid Visa
            "5425233430109903",  # Valid Mastercard
            "4532-0151-1283-0366"  # With dashes
        ]
        invalid_cards = [
            "4532015112830367",  # Invalid Luhn
            "1234567890123456"   # Invalid pattern
        ]
        
        detector = RegexDetector()
        for card in valid_cards:
            detections = detector.detect(card)
            assert len(detections) == 1
            assert detections[0].type == PIIType.CREDIT_CARD
```

### 2.2 NER Detector Tests
```python
# tests/test_ner_detector.py
class TestNERDetector:
    def test_person_name_detection(self):
        """Test person name detection"""
        detector = NERDetector()
        text = "Meeting with John Smith and Jane Doe tomorrow"
        detections = detector.detect(text)
        
        person_detections = [d for d in detections if d.type == PIIType.PERSON]
        assert len(person_detections) == 2
        assert any(d.text == "John Smith" for d in person_detections)
        assert any(d.text == "Jane Doe" for d in person_detections)
    
    def test_organization_detection(self):
        """Test organization detection"""
        detector = NERDetector()
        text = "I work at Microsoft and previously at Google"
        detections = detector.detect(text)
        
        org_detections = [d for d in detections if d.type == PIIType.ORGANIZATION]
        assert len(org_detections) == 2
    
    def test_location_detection(self):
        """Test location detection"""
        detector = NERDetector()
        text = "Born in New York, now living in San Francisco"
        detections = detector.detect(text)
        
        loc_detections = [d for d in detections if d.type == PIIType.LOCATION]
        assert len(loc_detections) == 2
    
    def test_confidence_threshold(self):
        """Test confidence-based filtering"""
        detector = NERDetector(confidence_threshold=0.9)
        text = "Maybe John or possibly Jane"
        detections = detector.detect(text)
        
        # Should filter out low confidence detections
        assert all(d.confidence >= 0.9 for d in detections)
```

### 2.3 Masker Tests
```python
# tests/test_maskers.py
class TestSimpleMasker:
    def test_type_aware_masking(self):
        """Test type-aware placeholder masking"""
        masker = SimpleMasker(format=MaskFormat.TYPE_AWARE)
        text = "Email: john@example.com"
        detections = [
            Detection(PIIType.EMAIL, 7, 23, "john@example.com", 0.95, "regex")
        ]
        
        masked = masker.mask(text, detections)
        assert masked == "Email: [EMAIL]"
    
    def test_length_preserving_masking(self):
        """Test length-preserving masking"""
        masker = SimpleMasker(format=MaskFormat.LENGTH_PRESERVING)
        text = "SSN: 123-45-6789"
        detections = [
            Detection(PIIType.SSN, 5, 16, "123-45-6789", 0.95, "regex")
        ]
        
        masked = masker.mask(text, detections)
        assert masked == "SSN: ***********"
        assert len(masked) == len(text)
    
    def test_multiple_detections(self):
        """Test masking with multiple detections"""
        masker = SimpleMasker()
        text = "Call John at 555-1234 or email john@example.com"
        detections = [
            Detection(PIIType.PERSON, 5, 9, "John", 0.9, "ner"),
            Detection(PIIType.PHONE, 13, 21, "555-1234", 0.95, "regex"),
            Detection(PIIType.EMAIL, 31, 47, "john@example.com", 0.95, "regex")
        ]
        
        masked = masker.mask(text, detections)
        assert masked == "Call [PERSON] at [PHONE] or email [EMAIL]"

class TestReversibleMasker:
    def test_reversible_masking(self):
        """Test token-based reversible masking"""
        masker = ReversibleMasker()
        text = "Contact john@example.com for details"
        detections = [
            Detection(PIIType.EMAIL, 8, 24, "john@example.com", 0.95, "regex")
        ]
        
        masked = masker.mask(text, detections)
        assert "[EMAIL:" in masked
        assert masked.startswith("Contact [EMAIL:")
        assert masked.endswith("] for details")
        
        # Test unmasking
        unmasked = masker.unmask(masked)
        assert unmasked == text
```

### 2.4 Parser Tests
```python
# tests/test_parsers.py
class TestJSONParser:
    def test_simple_json_parsing(self):
        """Test basic JSON structure parsing"""
        parser = JSONParser()
        data = {"name": "John Doe", "email": "john@example.com"}
        
        chunks = parser.parse(data)
        assert len(chunks) == 2
        assert any(c.text == "John Doe" for c in chunks)
        assert any(c.text == "john@example.com" for c in chunks)
    
    def test_nested_json_parsing(self):
        """Test nested JSON structure"""
        parser = JSONParser()
        data = {
            "user": {
                "personal": {
                    "name": "John Doe",
                    "ssn": "123-45-6789"
                },
                "contact": {
                    "email": "john@example.com"
                }
            }
        }
        
        chunks = parser.parse(data)
        assert len(chunks) == 3
        
        # Verify paths are preserved
        for chunk in chunks:
            assert chunk.metadata['path'] is not None
    
    def test_json_reconstruction(self):
        """Test JSON reconstruction with masked values"""
        parser = JSONParser()
        original = {"name": "John Doe", "email": "john@example.com"}
        
        chunks = parser.parse(original)
        masked_texts = ["[PERSON]", "[EMAIL]"]
        
        result = parser.reconstruct(chunks, masked_texts)
        assert result == {"name": "[PERSON]", "email": "[EMAIL]"}

class TestHTMLParser:
    def test_html_text_extraction(self):
        """Test HTML text node extraction"""
        parser = HTMLParser()
        html = "<p>Contact <a href='mailto:john@example.com'>John Doe</a></p>"
        
        chunks = parser.parse(html)
        text_chunks = [c for c in chunks if not c.metadata.get('is_attribute')]
        assert len(text_chunks) >= 2
    
    def test_html_attribute_extraction(self):
        """Test HTML attribute extraction"""
        parser = HTMLParser()
        html = '<input type="email" value="john@example.com" placeholder="Enter email">'
        
        chunks = parser.parse(html)
        attr_chunks = [c for c in chunks if c.metadata.get('is_attribute')]
        assert any(c.text == "john@example.com" for c in attr_chunks)
    
    def test_html_reconstruction(self):
        """Test HTML reconstruction preserves structure"""
        parser = HTMLParser()
        html = "<p>Email: <span>john@example.com</span></p>"
        
        chunks = parser.parse(html)
        # Mask only the email text
        masked_texts = [c.text if "@" not in c.text else "[EMAIL]" for c in chunks]
        
        result = parser.reconstruct(chunks, masked_texts)
        assert "<p>" in result
        assert "<span>" in result
        assert "[EMAIL]" in result
```

## 3. Integration Tests

### 3.1 End-to-End Tests
```python
# tests/test_integration.py
class TestSanitizerIntegration:
    def test_text_sanitization_e2e(self):
        """Test complete text sanitization flow"""
        sanitizer = Sanitizer()
        text = """
        Personal Information:
        Name: John Doe
        Email: john.doe@example.com
        Phone: (555) 123-4567
        SSN: 123-45-6789
        """
        
        result = sanitizer.sanitize(text)
        assert "[PERSON]" in result
        assert "[EMAIL]" in result
        assert "[PHONE]" in result
        assert "[SSN]" in result
        assert "john.doe@example.com" not in result
    
    def test_json_sanitization_e2e(self):
        """Test JSON sanitization preserves structure"""
        sanitizer = Sanitizer()
        data = {
            "employee": {
                "name": "Jane Smith",
                "contact": {
                    "email": "jane@company.com",
                    "phone": "555-0123"
                }
            }
        }
        
        result = sanitizer.sanitize(data, format="json")
        assert isinstance(result, dict)
        assert result["employee"]["name"] == "[PERSON]"
        assert result["employee"]["contact"]["email"] == "[EMAIL]"
        assert result["employee"]["contact"]["phone"] == "[PHONE]"
    
    def test_html_sanitization_e2e(self):
        """Test HTML sanitization preserves markup"""
        sanitizer = Sanitizer()
        html = """
        <div class="contact">
            <h1>Contact Information</h1>
            <p>Name: <strong>John Doe</strong></p>
            <p>Email: <a href="mailto:john@example.com">john@example.com</a></p>
        </div>
        """
        
        result = sanitizer.sanitize(html, format="html")
        assert "<div" in result
        assert "<strong>[PERSON]</strong>" in result
        assert "john@example.com" not in result
        assert "[EMAIL]" in result
```

### 3.2 Detection Merging Tests
```python
class TestDetectionMerging:
    def test_overlapping_detections(self):
        """Test handling of overlapping detections"""
        sanitizer = Sanitizer()
        text = "Dr. John Smith, MD"  # Both title and name
        
        detections = sanitizer.detect_pii(text)
        # Should merge overlapping detections intelligently
        assert len(detections) <= 2  # Not more than name + title
    
    def test_conflict_resolution(self):
        """Test conflict resolution between detectors"""
        sanitizer = Sanitizer()
        text = "Contact support@example.com"  # Could be email or organization
        
        detections = sanitizer.detect_pii(text)
        # Should prefer high-confidence detection
        email_detections = [d for d in detections if d.type == PIIType.EMAIL]
        assert len(email_detections) == 1
```

## 4. Performance Tests

### 4.1 Latency Tests
```python
# tests/test_performance.py
import time
import pytest

class TestPerformance:
    def test_latency_small_document(self):
        """Test <100ms latency for small documents"""
        sanitizer = Sanitizer()
        text = "John Doe's email is john@example.com" * 10  # ~400 chars
        
        start = time.time()
        result = sanitizer.sanitize(text)
        elapsed = (time.time() - start) * 1000  # ms
        
        assert elapsed < 100
        assert "[EMAIL]" in result
    
    def test_latency_medium_document(self):
        """Test latency for medium documents"""
        sanitizer = Sanitizer()
        text = generate_test_document(size_kb=5)
        
        start = time.time()
        result = sanitizer.sanitize(text)
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 100  # Should still be under 100ms
    
    @pytest.mark.performance
    def test_throughput(self):
        """Test throughput for batch processing"""
        sanitizer = Sanitizer()
        documents = [generate_test_document() for _ in range(100)]
        
        start = time.time()
        results = [sanitizer.sanitize(doc) for doc in documents]
        elapsed = time.time() - start
        
        throughput = len(documents) / elapsed
        assert throughput >= 100  # At least 100 docs/second
    
    def test_memory_usage(self):
        """Test memory footprint stays under limit"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        sanitizer = Sanitizer()
        # Process many documents
        for _ in range(100):
            text = generate_test_document()
            sanitizer.sanitize(text)
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        assert memory_increase < 100  # Less than 100MB increase
```

### 4.2 Stress Tests
```python
class TestStress:
    def test_large_document_handling(self):
        """Test handling of large documents"""
        sanitizer = Sanitizer()
        # 5MB document
        large_text = "John Doe john@example.com " * 100000
        
        result = sanitizer.sanitize(large_text)
        assert "[PERSON]" in result
        assert "[EMAIL]" in result
    
    def test_concurrent_requests(self):
        """Test concurrent processing"""
        import concurrent.futures
        
        sanitizer = Sanitizer()
        documents = [generate_test_document() for _ in range(50)]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(sanitizer.sanitize, doc) for doc in documents]
            results = [f.result() for f in futures]
        
        assert len(results) == 50
        assert all("[" in r for r in results)  # All should have masks
```

## 5. Edge Case Tests

### 5.1 Input Validation Tests
```python
class TestInputValidation:
    def test_empty_input(self):
        """Test handling of empty input"""
        sanitizer = Sanitizer()
        assert sanitizer.sanitize("") == ""
        assert sanitizer.sanitize({}) == {}
    
    def test_invalid_format(self):
        """Test handling of invalid formats"""
        sanitizer = Sanitizer()
        result = sanitizer.sanitize("{invalid json", format="json")
        # Should fall back to text processing
        assert isinstance(result, str)
    
    def test_encoding_issues(self):
        """Test handling of encoding issues"""
        sanitizer = Sanitizer()
        text = "Café owner José's email: josé@café.com"
        result = sanitizer.sanitize(text)
        assert "[EMAIL]" in result
    
    def test_binary_data(self):
        """Test handling of binary data"""
        sanitizer = Sanitizer()
        binary = b"\x00\x01\x02Hello john@example.com"
        # Should handle gracefully
        result = sanitizer.sanitize(binary.decode('utf-8', errors='ignore'))
        assert "[EMAIL]" in result
```

### 5.2 Boundary Tests
```python
class TestBoundaries:
    def test_partial_pii_detection(self):
        """Test partial PII at boundaries"""
        sanitizer = Sanitizer()
        test_cases = [
            "Email: john@ex",  # Incomplete email
            "Phone: 555-12",   # Incomplete phone
            "SSN: 123-45-",    # Incomplete SSN
        ]
        
        for text in test_cases:
            result = sanitizer.sanitize(text)
            # Should not detect partial PII
            assert "[" not in result
    
    def test_pii_in_urls(self):
        """Test PII detection in URLs"""
        sanitizer = Sanitizer()
        text = "Visit https://example.com/users/john.doe@example.com/profile"
        result = sanitizer.sanitize(text)
        # Should detect email even in URL
        assert "[EMAIL]" in result
```

## 6. Test Utilities

### 6.1 Test Data Generation
```python
# tests/utils.py
def generate_test_document(size_kb=1, pii_density=0.1):
    """Generate test documents with known PII"""
    pii_templates = [
        "Contact {name} at {email}",
        "Call {name} at {phone}",
        "{name}'s SSN is {ssn}",
        "Send payment to {credit_card}"
    ]
    
    names = ["John Doe", "Jane Smith", "Bob Johnson"]
    emails = ["john@example.com", "jane@company.org", "bob@test.net"]
    phones = ["555-123-4567", "(555) 987-6543", "+1 555 234 5678"]
    ssns = ["123-45-6789", "987-65-4321", "111-22-3333"]
    
    # Generate document with controlled PII density
    # ...implementation...
    
def assert_no_pii(text):
    """Assert text contains no PII patterns"""
    patterns = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit card
    ]
    
    for pattern in patterns:
        assert not re.search(pattern, text), f"Found PII matching {pattern}"
```

## 7. Test Execution Strategy

### 7.1 Test Phases
1. **Unit Tests First**: Run all unit tests for individual components
2. **Integration Tests**: Test component interactions
3. **Performance Tests**: Validate performance requirements
4. **Edge Case Tests**: Ensure robustness
5. **Regression Tests**: Run on every change

### 7.2 CI/CD Integration
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run unit tests
        run: pytest tests/unit -v --cov=maskingengine
      - name: Run integration tests
        run: pytest tests/integration -v
      - name: Run performance tests
        run: pytest tests/performance -v -m performance
      - name: Generate coverage report
        run: coverage report --fail-under=90
```

### 7.3 Test Coverage Goals
- Overall coverage: >90%
- Core modules: >95%
- Critical paths: 100%
- Edge cases: >85%