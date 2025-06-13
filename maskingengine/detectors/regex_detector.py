"""Regex-based PII detection for high-confidence patterns."""

import re
from typing import List, Tuple, Set
import phonenumbers
from phonenumbers import NumberParseException


class RegexDetector:
    """Detects structured PII using high-confidence regex patterns."""
    
    def __init__(self):
        self.patterns = {
            "EMAIL": re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                re.IGNORECASE
            ),
            "CREDIT_CARD": re.compile(
                r'\b(?:'
                r'4[0-9]{12}(?:[0-9]{3})?|'  # Visa
                r'5[1-5][0-9]{14}|'  # MasterCard
                r'3[47][0-9]{13}|'  # American Express
                r'3(?:0[0-5]|[68][0-9])[0-9]{11}|'  # Diners Club
                r'6(?:011|5[0-9]{2})[0-9]{12}|'  # Discover
                r'(?:2131|1800|35\d{3})\d{11}'  # JCB
                r')\b'
            ),
            "IPV4": re.compile(
                r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
                r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
            ),
            "IPV6": re.compile(
                r'(?:(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|'
                r'(?:[0-9a-fA-F]{1,4}:){1,7}:|'
                r'(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|'
                r'(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|'
                r'(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|'
                r'(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|'
                r'(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|'
                r'[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|'
                r':(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|'
                r'fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|'
                r'::(?:ffff(?::0{1,4}){0,1}:){0,1}'
                r'(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}'
                r'(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|'
                r'(?:[0-9a-fA-F]{1,4}:){1,4}:'
                r'(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}'
                r'(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9]))'
            ),
            "PHONE": re.compile(
                r'(?:\+?[1-9]\d{0,2}[\s.-]?)?'
                r'(?:\(?\d{1,4}\)?[\s.-]?)?'
                r'\d{1,4}[\s.-]?\d{1,4}[\s.-]?\d{1,9}'
            )
        }
    
    def detect(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        Detect PII patterns in text.
        
        Args:
            text: Input text to scan
            
        Returns:
            List of tuples (entity_type, matched_text, start_pos, end_pos)
        """
        detections = []
        
        for entity_type, pattern in self.patterns.items():
            if entity_type == "PHONE":
                detections.extend(self._detect_phones(text))
            else:
                for match in pattern.finditer(text):
                    if entity_type == "CREDIT_CARD" and not self._validate_credit_card(match.group()):
                        continue
                    detections.append((
                        entity_type,
                        match.group(),
                        match.start(),
                        match.end()
                    ))
        
        return self._deduplicate_detections(detections)
    
    def _detect_phones(self, text: str) -> List[Tuple[str, str, int, int]]:
        """Detect phone numbers using phonenumbers library for better accuracy."""
        detections = []
        
        # First, use regex to find potential phone numbers
        for match in self.patterns["PHONE"].finditer(text):
            phone_text = match.group()
            
            # Try to parse with phonenumbers library
            try:
                # Try with common country codes
                for country in [None, "US", "GB", "DE", "FR", "ES", "IT", "JP", "CN", "IN"]:
                    try:
                        parsed = phonenumbers.parse(phone_text, country)
                        if phonenumbers.is_valid_number(parsed):
                            detections.append((
                                "PHONE",
                                phone_text,
                                match.start(),
                                match.end()
                            ))
                            break
                    except NumberParseException:
                        continue
            except Exception:
                # If phonenumbers fails, fall back to regex match for numbers that look like phones
                if len(re.sub(r'\D', '', phone_text)) >= 7:
                    detections.append((
                        "PHONE",
                        phone_text,
                        match.start(),
                        match.end()
                    ))
        
        return detections
    
    def _validate_credit_card(self, card_number: str) -> bool:
        """Validate credit card number using Luhn algorithm."""
        # Remove non-digits
        card_number = re.sub(r'\D', '', card_number)
        
        if not card_number or len(card_number) < 13:
            return False
        
        # Luhn algorithm
        total = 0
        reverse_digits = card_number[::-1]
        
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        
        return total % 10 == 0
    
    def _deduplicate_detections(self, detections: List[Tuple[str, str, int, int]]) -> List[Tuple[str, str, int, int]]:
        """Remove overlapping detections, keeping the longer match."""
        if not detections:
            return []
        
        # Sort by start position and then by length (descending)
        sorted_detections = sorted(detections, key=lambda x: (x[2], -(x[3] - x[2])))
        
        result = []
        last_end = -1
        
        for detection in sorted_detections:
            if detection[2] >= last_end:
                result.append(detection)
                last_end = detection[3]
        
        return result