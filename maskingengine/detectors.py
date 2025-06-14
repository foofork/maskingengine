"""Simplified detectors module with regex and NER detection."""

import re
from typing import List, Tuple, Optional
from .config import Config


class Detection:
    """Simple detection result tuple."""
    def __init__(self, type_: str, text: str, start: int, end: int):
        self.type = type_
        self.text = text
        self.start = start
        self.end = end
    
    def as_tuple(self) -> Tuple[str, str, int, int]:
        """Return as tuple for backward compatibility."""
        return (self.type, self.text, self.start, self.end)


class RegexDetector:
    """Fast regex-based PII detection."""
    
    def __init__(self, patterns: Optional[dict] = None):
        self.patterns = patterns or Config.PATTERNS
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile all regex patterns."""
        compiled = {}
        for name, pattern in self.patterns.items():
            compiled[name] = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        return compiled
    
    def detect(self, text: str) -> List[Tuple[str, str, int, int]]:
        """Detect PII using regex patterns."""
        detections = []
        
        for pii_type, pattern in self.compiled_patterns.items():
            for match in pattern.finditer(text):
                # Special validation for credit cards (Luhn check)
                if pii_type == 'CREDIT_CARD':
                    if not self._luhn_check(match.group()):
                        continue
                
                detections.append((
                    pii_type,
                    match.group(),
                    match.start(),
                    match.end()
                ))
        
        return detections
    
    def _luhn_check(self, card_number: str) -> bool:
        """Validate credit card using Luhn algorithm."""
        # Remove non-digits
        digits = re.sub(r'\D', '', card_number)
        
        if len(digits) < 13 or len(digits) > 19:
            return False
        
        # Luhn algorithm
        total = 0
        reverse_digits = digits[::-1]
        
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:  # Every second digit from right
                n *= 2
                if n > 9:
                    n = n // 10 + n % 10
            total += n
        
        return total % 10 == 0


class NERDetector:
    """NER-based entity detection with lazy loading."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or Config.NER_MODEL_PATH
        self._model = None
        self._model_loading = False
    
    @property
    def model(self):
        """Lazy load NER model."""
        if self._model is None and not self._model_loading:
            self._model_loading = True
            try:
                import spacy
                self._model = spacy.load(self.model_path)
            except (ImportError, OSError):
                # Model not available, disable NER
                self._model = None
            finally:
                self._model_loading = False
        return self._model
    
    def detect(self, text: str) -> List[Tuple[str, str, int, int]]:
        """Detect entities using NER model."""
        if not self.model:
            return []  # Skip if model not available
        
        # Quick filter to avoid NER overhead
        if len(text) < 10 or not self._has_potential_entities(text):
            return []
        
        try:
            doc = self.model(text)
            detections = []
            
            for ent in doc.ents:
                # Filter by entity type and length
                if (ent.label_ in ['PERSON', 'ORG', 'GPE'] and 
                    len(ent.text.strip()) > 2):
                    
                    detections.append((
                        ent.label_,
                        ent.text,
                        ent.start_char,
                        ent.end_char
                    ))
            
            return detections
            
        except Exception:
            # Graceful degradation on NER failure
            return []
    
    def _has_potential_entities(self, text: str) -> bool:
        """Quick heuristic check for potential proper nouns."""
        return re.search(r'\b[A-Z][a-z]+', text) is not None


class Detector:
    """Main detector that combines regex and NER."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.regex_detector = RegexDetector(self.config.PATTERNS)
        self.ner_detector = NERDetector(self.config.NER_MODEL_PATH) if self.config.NER_ENABLED else None
    
    def detect_all(self, text: str) -> List[Tuple[str, str, int, int]]:
        """Detect all PII using both regex and NER."""
        # Start with regex (fast)
        detections = self.regex_detector.detect(text)
        
        # Add NER detections if enabled
        if self.ner_detector:
            ner_detections = self.ner_detector.detect(text)
            detections.extend(ner_detections)
        
        # Deduplicate overlapping detections
        return self._deduplicate(detections)
    
    def _deduplicate(self, detections: List[Tuple[str, str, int, int]]) -> List[Tuple[str, str, int, int]]:
        """Remove overlapping detections, keeping the best ones."""
        if not detections:
            return []
        
        # Sort by start position, then by priority
        sorted_detections = sorted(detections, key=lambda d: (d[2], self._get_type_priority(d[0])))
        
        # Remove overlaps
        result = []
        last_end = -1
        
        for detection in sorted_detections:
            start = detection[2]
            end = detection[3]
            
            if start >= last_end:  # No overlap
                result.append(detection)
                last_end = end
            else:
                # Overlap - keep the one with higher priority
                if result and self._get_type_priority(detection[0]) > self._get_type_priority(result[-1][0]):
                    result[-1] = detection
                    last_end = end
        
        return result
    
    def _get_type_priority(self, pii_type: str) -> int:
        """Get priority for PII type (higher = more specific/important)."""
        priority_map = {
            'EMAIL': 10, 'SSN': 10, 'CREDIT_CARD': 10,  # High confidence structured
            'PHONE': 8, 'PHONE_US': 8, 'IPV4': 8, 'IPV6': 8,  # Medium confidence
            'PERSON': 5, 'ORG': 5, 'ORGANIZATION': 5, 'GPE': 5, 'LOCATION': 5  # NER types
        }
        return priority_map.get(pii_type, 1)