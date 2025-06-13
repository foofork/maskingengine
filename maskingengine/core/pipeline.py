"""Core sanitization pipeline implementation."""

import logging
from typing import List, Tuple, Dict, Any, Optional, Set
import re

from ..detectors.regex_detector import RegexDetector
from ..detectors.ner_detector import NERDetector
from .config import SanitizerConfig
from .parsers import BaseParser, PlainTextParser, JSONParser, HTMLParser


class SanitizationPipeline:
    """Main pipeline for detecting and sanitizing PII."""
    
    def __init__(self, config: SanitizerConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize detectors
        self.regex_detector = RegexDetector() if config.enable_regex else None
        self.ner_detector = NERDetector() if config.enable_ner else None
        
        # Initialize parsers
        self.parsers = {
            "text": PlainTextParser(),
            "json": JSONParser(),
            "html": HTMLParser()
        }
        
        # Compile whitelist patterns
        self._compile_whitelist_patterns()
    
    def _compile_whitelist_patterns(self):
        """Compile whitelist entries into regex patterns."""
        self.whitelist_patterns = []
        for entry in self.config.whitelist:
            # Escape special regex characters and create word boundary pattern
            escaped = re.escape(entry)
            pattern = re.compile(rf'\b{escaped}\b', re.IGNORECASE)
            self.whitelist_patterns.append(pattern)
    
    def process(self, content: str, content_type: str = "text") -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Process content through the sanitization pipeline.
        
        Args:
            content: Input content to sanitize
            content_type: Type of content (text, json, html)
            
        Returns:
            Tuple of (sanitized_text, detections, parser_metadata)
        """
        # Validate input
        if len(content) > self.config.max_input_characters:
            raise ValueError(f"Input exceeds maximum length of {self.config.max_input_characters} characters")
        
        # Select parser
        parser = self.parsers.get(content_type, self.parsers["text"])
        
        # Parse content
        try:
            text, parser_metadata = parser.parse(content)
        except ValueError as e:
            self.logger.error(f"Failed to parse {content_type}: {e}")
            raise
        
        # Detect PII
        all_detections = []
        
        if self.config.enable_regex and self.regex_detector:
            regex_detections = self.regex_detector.detect(text)
            all_detections.extend([
                {
                    "type": det[0],
                    "text": det[1],
                    "start": det[2],
                    "end": det[3],
                    "confidence": 1.0,
                    "source": "regex"
                }
                for det in regex_detections
            ])
        
        if self.config.enable_ner and self.ner_detector:
            ner_detections = self.ner_detector.detect(text, self.config.confidence_threshold)
            all_detections.extend([
                {
                    "type": det[0],
                    "text": det[1],
                    "start": det[2],
                    "end": det[3],
                    "confidence": det[4],
                    "source": "ner"
                }
                for det in ner_detections
            ])
        
        # Apply whitelist filtering
        filtered_detections = self._apply_whitelist(all_detections, text)
        
        # Sort by position for consistent processing
        filtered_detections.sort(key=lambda x: x["start"])
        
        return text, filtered_detections, parser_metadata
    
    def _apply_whitelist(self, detections: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """Filter out whitelisted detections."""
        filtered = []
        
        for detection in detections:
            # Check if detection matches any whitelist pattern
            is_whitelisted = False
            detection_text = detection["text"]
            
            for pattern in self.whitelist_patterns:
                if pattern.search(detection_text):
                    is_whitelisted = True
                    if self.config.logging_enabled:
                        self.logger.debug(f"Whitelisted: {detection_text}")
                    break
            
            if not is_whitelisted:
                filtered.append(detection)
        
        return filtered
    
    def deduplicate_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate and overlapping detections."""
        if not detections:
            return []
        
        # Sort by start position
        sorted_detections = sorted(detections, key=lambda x: (x["start"], -x["end"]))
        
        result = []
        last_end = -1
        
        for detection in sorted_detections:
            # Skip if overlapping with previous detection
            if detection["start"] >= last_end:
                result.append(detection)
                last_end = detection["end"]
            elif detection["end"] > last_end:
                # Partial overlap - adjust start position
                adjusted = detection.copy()
                adjusted["start"] = last_end
                adjusted["text"] = detection["text"][last_end - detection["start"]:]
                if adjusted["text"]:  # Only add if there's still text
                    result.append(adjusted)
                    last_end = adjusted["end"]
        
        return result