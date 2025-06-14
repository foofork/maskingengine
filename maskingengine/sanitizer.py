"""Simplified sanitizer class for minimal architecture."""

import time
from typing import Union, Dict, Any, Optional
from .config import Config
from .parsers import Parser, JSONParser, HTMLParser
from .detectors import Detector
from .masker import Masker


class Sanitizer:
    """Main sanitizer class with simple synchronous API."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize sanitizer with configuration."""
        self.config = config or Config()
        self.detector = Detector(self.config)
        self.masker = Masker(self.config.TYPE_HASHES)
    
    def sanitize(self, input_data: Union[str, Dict, Any], format: Optional[str] = None) -> Union[str, Dict]:
        """
        Sanitize input data by detecting and masking PII.
        
        Args:
            input_data: Text string, JSON dict, or HTML string
            format: Optional format hint ("text", "json", "html", or None for auto-detect)
            
        Returns:
            Sanitized data in same format as input
            
        Raises:
            ValueError: If input is too large or invalid
        """
        start_time = time.time()
        
        try:
            # Validate input size
            input_str = str(input_data)
            if len(input_str) > self.config.MAX_TEXT_LENGTH:
                raise ValueError(f"Input too large: {len(input_str)} > {self.config.MAX_TEXT_LENGTH}")
            
            # Parse input based on format
            if format == "json" or (format is None and isinstance(input_data, dict)):
                return self._sanitize_json(input_data)
            elif format == "html" or (format is None and isinstance(input_data, str) and self._is_html(input_data)):
                return self._sanitize_html(input_data)
            else:
                return self._sanitize_text(str(input_data))
                
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            # Graceful degradation for other errors
            return str(input_data)  # Return original on error
        finally:
            # Performance monitoring
            elapsed = (time.time() - start_time) * 1000
            if elapsed > 100:  # Warn if over 100ms
                print(f"Warning: Processing took {elapsed:.1f}ms")
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize plain text."""
        # Detect PII
        detections = self.detector.detect_all(text)
        
        # Apply masking
        return self.masker.mask(text, detections)
    
    def _sanitize_json(self, data: Union[str, dict]) -> dict:
        """Sanitize JSON data while preserving structure."""
        # Parse JSON if string
        if isinstance(data, str):
            import json
            parsed_data = json.loads(data)
        else:
            parsed_data = data
        
        # Extract text chunks
        chunks = Parser.parse(parsed_data)
        
        # Process each chunk
        masked_texts = []
        for chunk in chunks:
            detections = self.detector.detect_all(chunk.text)
            masked_text = self.masker.mask(chunk.text, detections)
            masked_texts.append(masked_text)
        
        # Reconstruct JSON
        return JSONParser.reconstruct(parsed_data, chunks, masked_texts)
    
    def _sanitize_html(self, html: str) -> str:
        """Sanitize HTML while preserving markup."""
        # Extract text chunks
        chunks = HTMLParser.parse(html)
        
        # Process each chunk
        masked_texts = []
        for chunk in chunks:
            detections = self.detector.detect_all(chunk.text)
            masked_text = self.masker.mask(chunk.text, detections)
            masked_texts.append(masked_text)
        
        # Reconstruct HTML
        return HTMLParser.reconstruct(html, chunks, masked_texts)
    
    def _is_html(self, text: str) -> bool:
        """Quick heuristic to detect HTML content."""
        return '<' in text[:100] and '>' in text[:100] and any(
            tag in text.lower() for tag in ['<html', '<body', '<div', '<p>', '<span', '<a ']
        )