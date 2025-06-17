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
    """Fast regex-based PII detection with pattern pack support."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.patterns = self.config.PATTERNS
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile all regex patterns with error handling."""
        compiled = {}
        for name, patterns in self.patterns.items():
            compiled_patterns = []
            
            # Handle both single pattern strings and lists of patterns
            pattern_list = patterns if isinstance(patterns, list) else [patterns] if isinstance(patterns, str) else []
            
            for pattern in pattern_list:
                try:
                    compiled_pattern = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                    compiled_patterns.append(compiled_pattern)
                except re.error as e:
                    print(f"Warning: Invalid regex pattern in {name}: {pattern} - {e}")
                    continue  # Skip invalid patterns
                except Exception as e:
                    print(f"Warning: Unexpected error compiling pattern in {name}: {pattern} - {e}")
                    continue
            
            compiled[name] = compiled_patterns
        return compiled
    
    
    def detect(self, text: str) -> List[Tuple[str, str, int, int]]:
        """Detect PII using regex patterns with context validation."""
        detections = []
        
        for pii_type, patterns in self.compiled_patterns.items():
            # Iterate through all patterns for this PII type
            for pattern in patterns:
                for match in pattern.finditer(text):
                    matched_text = match.group()
                    start, end = match.start(), match.end()
                    
                    # Skip if in whitelist
                    if matched_text.lower() in {w.lower() for w in self.config.whitelist}:
                        continue
                    
                    # Special validation for credit cards (Luhn check)
                    if pii_type.upper() in ['CREDIT_CARD', 'CREDIT_CARD_NUMBER'] and self.config.strict_validation:
                        if not self._luhn_check(matched_text):
                            continue
                    
                    detections.append((
                        pii_type,
                        matched_text,
                        start,
                        end
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
    """NER-based entity detection using DistilBERT for multilingual PII detection."""
    
    def __init__(self, model_path: Optional[str] = None, min_confidence: Optional[float] = None, config: Optional[Config] = None):
        self.model_path = model_path or Config.NER_MODEL_PATH
        self.min_confidence = min_confidence or Config.NER_MIN_CONFIDENCE
        self.config = config or Config()
        self._tokenizer = None
        self._model = None
        self._model_loading = False
    
    @property
    def model(self):
        """Lazy load NER model and tokenizer."""
        if self._model is None and not self._model_loading:
            self._model_loading = True
            try:
                from transformers import AutoTokenizer, AutoModelForTokenClassification
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                self._model = AutoModelForTokenClassification.from_pretrained(self.model_path)
            except (ImportError, OSError, Exception):
                # Model not available, disable NER
                self._model = None
                self._tokenizer = None
            finally:
                self._model_loading = False
        return self._model
    
    @property
    def tokenizer(self):
        """Get tokenizer (ensures model is loaded first)."""
        _ = self.model  # Trigger model loading
        return self._tokenizer
    
    def detect(self, text: str) -> List[Tuple[str, str, int, int]]:
        """Detect entities using DistilBERT NER model."""
        if not self.model or not self.tokenizer:
            return []  # Skip if model not available
        
        # Quick filter to avoid NER overhead
        if len(text) < 10 or not self._has_potential_entities(text):
            return []
        
        try:
            import torch
            from transformers import pipeline
            
            # Create NER pipeline
            ner_pipeline = pipeline(
                "ner",
                model=self.model,
                tokenizer=self.tokenizer,
                aggregation_strategy="simple",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Run inference
            entities = ner_pipeline(text)
            detections = []
            
            for entity in entities:
                # Filter by confidence threshold
                if entity['score'] >= self.min_confidence and len(entity['word'].strip()) > 1:
                    
                    # Map entity types to our format
                    entity_type = self._map_entity_type(entity['entity_group'])
                    
                    # Get the actual text from the original string
                    actual_text = text[entity['start']:entity['end']]
                    
                    # Skip if in whitelist
                    if actual_text.lower() in {w.lower() for w in self.config.whitelist}:
                        continue
                    
                    detections.append((
                        entity_type,
                        actual_text,
                        entity['start'],
                        entity['end']
                    ))
            
            return detections
            
        except Exception as e:
            # Graceful degradation on NER failure
            return []
    
    def _map_entity_type(self, entity_group: str) -> str:
        """Map DistilBERT PII model entity types to our standard format."""
        mapping = {
            'EMAIL': 'EMAIL',
            'TEL': 'PHONE', 
            'PHONE': 'PHONE',
            'SOCIALNUMBER': 'SSN',
            'SSN': 'SSN',
            'CREDIT_CARD': 'CREDIT_CARD',
            'PERSON': 'PERSON',
            'NAME': 'PERSON',
            'ORGANIZATION': 'ORGANIZATION',
            'ORG': 'ORGANIZATION',
            'LOCATION': 'LOCATION',
            'LOC': 'LOCATION',
            'ADDRESS': 'LOCATION',
            'DATE': 'DATE',
            'TIME': 'TIME'
        }
        return mapping.get(entity_group.upper(), entity_group.upper())
    
    def _has_potential_entities(self, text: str) -> bool:
        """Quick heuristic check for potential proper nouns."""
        return re.search(r'\b[A-Z][a-z]+', text) is not None


class Detector:
    """Main detector that combines regex and NER."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.regex_detector = RegexDetector(self.config)
        self.ner_detector = NERDetector(
            self.config.NER_MODEL_PATH, 
            self.config.NER_MIN_CONFIDENCE,
            self.config
        ) if self.config.NER_ENABLED else None
    
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