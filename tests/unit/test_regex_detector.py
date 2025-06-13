"""Unit tests for regex-based PII detection following TDD principles."""

import pytest
from maskingengine.detectors.regex_detector import RegexDetector


class TestRegexDetector:
    """Test suite for RegexDetector class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = RegexDetector()
    
    # Email Detection Tests
    def test_detect_simple_email(self):
        """Test detection of simple email addresses."""
        text = "Contact me at john.doe@example.com"
        detections = self.detector.detect(text)
        
        assert len(detections) == 1
        assert detections[0][0] == "EMAIL"
        assert detections[0][1] == "john.doe@example.com"
        assert detections[0][2] == 14  # start position
        assert detections[0][3] == 35  # end position
    
    def test_detect_multiple_emails(self):
        """Test detection of multiple email addresses."""
        text = "Email alice@test.com or bob@example.org for details"
        detections = self.detector.detect(text)
        
        assert len(detections) == 2
        assert detections[0][1] == "alice@test.com"
        assert detections[1][1] == "bob@example.org"
    
    def test_email_with_special_chars(self):
        """Test email detection with special characters."""
        text = "Contact user+tag@sub.example.com"
        detections = self.detector.detect(text)
        
        assert len(detections) == 1
        assert detections[0][1] == "user+tag@sub.example.com"
    
    # Phone Number Detection Tests
    def test_detect_us_phone_number(self):
        """Test detection of US phone numbers."""
        text = "Call me at 555-123-4567"
        detections = self.detector.detect(text)
        
        assert len(detections) == 1
        assert detections[0][0] == "PHONE"
        assert detections[0][1] == "555-123-4567"
    
    def test_detect_international_phone(self):
        """Test detection of international phone numbers."""
        text = "My number is +1-555-123-4567"
        detections = self.detector.detect(text)
        
        assert len(detections) == 1
        assert detections[0][0] == "PHONE"
        assert "+1-555-123-4567" in detections[0][1]
    
    def test_phone_various_formats(self):
        """Test phone detection with various formats."""
        texts = [
            "Call (555) 123-4567",
            "Phone: +44 20 7946 0958",
            "Mobile: +33 6 12 34 56 78",
            "Contact: 555.123.4567"
        ]
        
        for text in texts:
            detections = self.detector.detect(text)
            assert len(detections) == 1
            assert detections[0][0] == "PHONE"
    
    # Credit Card Detection Tests
    def test_detect_visa_card(self):
        """Test detection of Visa credit card numbers."""
        text = "Payment with 4111111111111111"
        detections = self.detector.detect(text)
        
        assert len(detections) == 1
        assert detections[0][0] == "CREDIT_CARD"
        assert detections[0][1] == "4111111111111111"
    
    def test_detect_mastercard(self):
        """Test detection of MasterCard numbers."""
        text = "Card: 5500000000000004"
        detections = self.detector.detect(text)
        
        assert len(detections) == 1
        assert detections[0][0] == "CREDIT_CARD"
        assert detections[0][1] == "5500000000000004"
    
    def test_invalid_credit_card_luhn(self):
        """Test that invalid credit cards (failing Luhn) are not detected."""
        text = "Invalid card: 4111111111111112"  # Invalid Luhn
        detections = self.detector.detect(text)
        
        assert len(detections) == 0
    
    # IP Address Detection Tests
    def test_detect_ipv4_address(self):
        """Test detection of IPv4 addresses."""
        text = "Server at 192.168.1.1"
        detections = self.detector.detect(text)
        
        assert len(detections) == 1
        assert detections[0][0] == "IPV4"
        assert detections[0][1] == "192.168.1.1"
    
    def test_detect_ipv6_address(self):
        """Test detection of IPv6 addresses."""
        text = "IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        detections = self.detector.detect(text)
        
        assert len(detections) == 1
        assert detections[0][0] == "IPV6"
        assert detections[0][1] == "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    
    # Edge Cases and Multiple Detections
    def test_overlapping_detections(self):
        """Test handling of overlapping detections."""
        text = "Contact john@example.com at john@example.com"
        detections = self.detector.detect(text)
        
        # Should detect both instances
        assert len(detections) == 2
    
    def test_mixed_pii_detection(self):
        """Test detection of multiple PII types in one text."""
        text = "Email john@test.com or call 555-123-4567 from 192.168.1.1"
        detections = self.detector.detect(text)
        
        assert len(detections) == 3
        types = [d[0] for d in detections]
        assert "EMAIL" in types
        assert "PHONE" in types
        assert "IPV4" in types
    
    def test_no_pii_detection(self):
        """Test that clean text returns no detections."""
        text = "This is a clean text with no PII information."
        detections = self.detector.detect(text)
        
        assert len(detections) == 0
    
    def test_deduplication(self):
        """Test that overlapping matches are deduplicated correctly."""
        # This would need to be tested with specific overlapping patterns
        text = "test@example.com test@example.com"
        detections = self.detector.detect(text)
        
        # Verify positions don't overlap
        for i in range(len(detections) - 1):
            assert detections[i][3] <= detections[i + 1][2]