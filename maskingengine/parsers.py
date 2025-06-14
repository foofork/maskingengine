"""Simplified parsers module for text, JSON, and HTML formats."""

import json
import re
import copy
from typing import List, Dict, Any, Union


class TextChunk:
    """Simple text chunk with position information."""
    def __init__(self, text: str, offset: int = 0, metadata: Dict = None):
        self.text = text
        self.offset = offset
        self.metadata = metadata or {}


class Parser:
    """Main parser class with auto-detection."""
    
    @staticmethod
    def parse(input_data: Union[str, Dict, Any]) -> List[TextChunk]:
        """Parse input and return text chunks."""
        # Auto-detect format
        if isinstance(input_data, dict):
            return JSONParser.parse(input_data)
        elif isinstance(input_data, str):
            if '<' in input_data[:100] and '>' in input_data[:100]:  # Quick HTML check
                return HTMLParser.parse(input_data)
            else:
                return TextParser.parse(input_data)
        else:
            # Convert to string and parse as text
            return TextParser.parse(str(input_data))


class TextParser:
    """Simple text parser."""
    
    @staticmethod
    def parse(text: str) -> List[TextChunk]:
        """Parse plain text into single chunk."""
        return [TextChunk(text=text, offset=0, metadata={'type': 'text'})]
    
    @staticmethod
    def reconstruct(chunks: List[TextChunk], masked_texts: List[str]) -> str:
        """Reconstruct text (just return the masked text)."""
        return masked_texts[0] if masked_texts else ""


class JSONParser:
    """Simple JSON parser."""
    
    @staticmethod
    def parse(data: Union[str, dict]) -> List[TextChunk]:
        """Parse JSON and extract text chunks with paths."""
        if isinstance(data, str):
            data = json.loads(data)
        
        chunks = []
        JSONParser._extract_values(data, chunks, [])
        return chunks
    
    @staticmethod
    def _extract_values(obj: Any, chunks: List[TextChunk], path: List):
        """Extract string values recursively."""
        if isinstance(obj, str):
            chunks.append(TextChunk(
                text=obj,
                offset=0,
                metadata={'type': 'json', 'path': path.copy()}
            ))
        elif isinstance(obj, dict):
            for key, value in obj.items():
                JSONParser._extract_values(value, chunks, path + [key])
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                JSONParser._extract_values(item, chunks, path + [i])
    
    @staticmethod
    def reconstruct(original: dict, chunks: List[TextChunk], masked_texts: List[str]) -> dict:
        """Reconstruct JSON with masked values."""
        result = copy.deepcopy(original)
        
        for chunk, masked_text in zip(chunks, masked_texts):
            if 'path' in chunk.metadata:
                JSONParser._set_by_path(result, chunk.metadata['path'], masked_text)
        
        return result
    
    @staticmethod
    def _set_by_path(obj: Any, path: List, value: str):
        """Set value in nested structure by path."""
        current = obj
        for key in path[:-1]:
            current = current[key]
        current[path[-1]] = value


class HTMLParser:
    """Simple HTML parser using regex."""
    
    # Pre-compiled patterns for performance
    TEXT_PATTERN = re.compile(r'>([^<]+)<', re.MULTILINE)
    ATTR_PATTERN = re.compile(r'(?:alt|title|value|placeholder|href)="([^"]*)"', re.IGNORECASE)
    
    @staticmethod
    def parse(html: str) -> List[TextChunk]:
        """Parse HTML and extract text chunks."""
        chunks = []
        
        # Extract text between tags
        for match in HTMLParser.TEXT_PATTERN.finditer(html):
            text = match.group(1).strip()
            if text and len(text) > 1:  # Skip whitespace and single chars
                chunks.append(TextChunk(
                    text=text,
                    offset=match.start(1),
                    metadata={'type': 'html', 'tag_text': True}
                ))
        
        # Extract relevant attributes
        for match in HTMLParser.ATTR_PATTERN.finditer(html):
            attr_value = match.group(1).strip()
            if attr_value and len(attr_value) > 2:
                chunks.append(TextChunk(
                    text=attr_value,
                    offset=match.start(1),
                    metadata={'type': 'html', 'tag_text': False}
                ))
        
        return chunks
    
    @staticmethod
    def reconstruct(original: str, chunks: List[TextChunk], masked_texts: List[str]) -> str:
        """Reconstruct HTML with masked values."""
        result = original
        
        # Sort by offset in reverse order for safe replacement
        chunk_pairs = list(zip(chunks, masked_texts))
        chunk_pairs.sort(key=lambda x: x[0].offset, reverse=True)
        
        # Apply replacements from right to left
        for chunk, replacement in chunk_pairs:
            start = chunk.offset
            end = start + len(chunk.text)
            result = result[:start] + replacement + result[end:]
        
        return result