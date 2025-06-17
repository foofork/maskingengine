"""Unit tests for the masking and rehydration engine following TDD principles."""

import pytest
from maskingengine.core.masking import MaskingEngine


class TestMaskingEngine:
    """Test suite for MaskingEngine class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.masker = MaskingEngine()
        self.custom_masker = MaskingEngine(prefix="[[", suffix="]]")
    
    # Basic Masking Tests
    def test_mask_single_detection(self):
        """Test masking of a single PII detection."""
        text = "Contact john@example.com for info"
        detections = [{
            "type": "EMAIL",
            "text": "john@example.com",
            "start": 8,
            "end": 24
        }]
        
        masked_text, rehydration_map = self.masker.mask_text(text, detections)
        
        assert "john@example.com" not in masked_text
        assert "<<EMAIL_" in masked_text
        assert ">>" in masked_text
        assert len(rehydration_map) == 1
        
        # Verify placeholder maps back to original
        placeholder = list(rehydration_map.keys())[0]
        assert rehydration_map[placeholder] == "john@example.com"
    
    def test_mask_multiple_detections(self):
        """Test masking of multiple PII detections."""
        text = "Email john@test.com or call 555-123-4567"
        detections = [
            {"type": "EMAIL", "text": "john@test.com", "start": 6, "end": 19},
            {"type": "PHONE", "text": "555-123-4567", "start": 28, "end": 40}
        ]
        
        masked_text, rehydration_map = self.masker.mask_text(text, detections)
        
        assert "john@test.com" not in masked_text
        assert "555-123-4567" not in masked_text
        assert "<<EMAIL_" in masked_text
        assert "<<PHONE_" in masked_text
        assert len(rehydration_map) == 2
    
    def test_deterministic_masking(self):
        """Test that same PII always gets same placeholder."""
        text1 = "Contact john@example.com"
        text2 = "Email: john@example.com please"
        
        detections1 = [{"type": "EMAIL", "text": "john@example.com", "start": 8, "end": 24}]
        detections2 = [{"type": "EMAIL", "text": "john@example.com", "start": 7, "end": 23}]
        
        masked1, map1 = self.masker.mask_text(text1, detections1)
        masked2, map2 = self.masker.mask_text(text2, detections2)
        
        # Same email should get same placeholder
        placeholder1 = list(map1.keys())[0]
        placeholder2 = list(map2.keys())[0]
        assert placeholder1 == placeholder2
    
    def test_custom_placeholder_format(self):
        """Test custom placeholder prefix/suffix."""
        text = "Contact john@example.com"
        detections = [{"type": "EMAIL", "text": "john@example.com", "start": 8, "end": 24}]
        
        masked_text, _ = self.custom_masker.mask_text(text, detections)
        
        assert "[[EMAIL_" in masked_text
        assert "]]" in masked_text
        assert "<<" not in masked_text
        assert ">>" not in masked_text
    
    # Rehydration Tests
    def test_rehydrate_single_placeholder(self):
        """Test rehydration of single placeholder."""
        masked_text = "Contact <<EMAIL_12345678>> for info"
        rehydration_map = {"<<EMAIL_12345678>>": "john@example.com"}
        
        original = self.masker.rehydrate_text(masked_text, rehydration_map)
        
        assert original == "Contact john@example.com for info"
    
    def test_rehydrate_multiple_placeholders(self):
        """Test rehydration of multiple placeholders."""
        masked_text = "Email <<EMAIL_abc123>> or call <<PHONE_def456>>"
        rehydration_map = {
            "<<EMAIL_abc123>>": "john@test.com",
            "<<PHONE_def456>>": "555-123-4567"
        }
        
        original = self.masker.rehydrate_text(masked_text, rehydration_map)
        
        assert original == "Email john@test.com or call 555-123-4567"
    
    def test_rehydrate_repeated_placeholders(self):
        """Test rehydration when same placeholder appears multiple times."""
        masked_text = "Email <<EMAIL_abc123>> and <<EMAIL_abc123>> again"
        rehydration_map = {"<<EMAIL_abc123>>": "john@test.com"}
        
        original = self.masker.rehydrate_text(masked_text, rehydration_map)
        
        assert original == "Email john@test.com and john@test.com again"
    
    def test_rehydrate_empty_map(self):
        """Test rehydration with empty map returns original text."""
        masked_text = "No placeholders here"
        
        original = self.masker.rehydrate_text(masked_text, {})
        
        assert original == masked_text
    
    # Validation Tests
    def test_validate_valid_rehydration_map(self):
        """Test validation of well-formed rehydration map."""
        valid_map = {
            "<<EMAIL_12345678>>": "john@example.com",
            "<<PHONE_87654321>>": "555-123-4567"
        }
        
        assert self.masker.validate_rehydration_map(valid_map) is True
    
    def test_validate_invalid_placeholder_format(self):
        """Test validation catches invalid placeholder format."""
        invalid_map = {
            "EMAIL_12345678": "john@example.com",  # Missing delimiters
            "<<PHONE_87654321>>": "555-123-4567"
        }
        
        assert self.masker.validate_rehydration_map(invalid_map) is False
    
    def test_validate_non_string_values(self):
        """Test validation catches non-string values."""
        invalid_map = {
            "<<EMAIL_12345678>>": ["john@example.com"],  # List instead of string
            "<<PHONE_87654321>>": 5551234567  # Number instead of string
        }
        
        assert self.masker.validate_rehydration_map(invalid_map) is False
    
    # Edge Cases
    def test_mask_empty_detections(self):
        """Test masking with no detections returns original text."""
        text = "No PII here"
        detections = []
        
        masked_text, rehydration_map = self.masker.mask_text(text, detections)
        
        assert masked_text == text
        assert rehydration_map == {}
    
    def test_mask_overlapping_detections(self):
        """Test masking handles overlapping detections correctly."""
        text = "Contact john.doe@example.com"
        detections = [
            {"type": "EMAIL", "text": "john.doe@example.com", "start": 8, "end": 28},
            {"type": "PERSON", "text": "john.doe", "start": 8, "end": 16}
        ]
        
        # Sort by reverse order should handle overlaps
        masked_text, rehydration_map = self.masker.mask_text(text, detections)
        
        # Should contain placeholders but not overlap
        assert "john.doe@example.com" not in masked_text
        assert len(rehydration_map) > 0
    
    def test_merge_rehydration_maps(self):
        """Test merging multiple rehydration maps."""
        map1 = {"<<EMAIL_abc>>": "john@test.com"}
        map2 = {"<<PHONE_def>>": "555-1234"}
        map3 = {"<<EMAIL_ghi>>": "jane@test.com"}
        
        merged = self.masker.merge_rehydration_maps(map1, map2, map3)
        
        assert len(merged) == 3
        assert merged["<<EMAIL_abc>>"] == "john@test.com"
        assert merged["<<PHONE_def>>"] == "555-1234"
        assert merged["<<EMAIL_ghi>>"] == "jane@test.com"