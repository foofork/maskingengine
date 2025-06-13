"""Content parsers for different asset types."""

import json
import html
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from html.parser import HTMLParser


class BaseParser(ABC):
    """Base class for content parsers."""
    
    @abstractmethod
    def parse(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """Parse content and return text with metadata."""
        pass
    
    @abstractmethod
    def reconstruct(self, text: str, metadata: Dict[str, Any]) -> str:
        """Reconstruct original format from text and metadata."""
        pass


class PlainTextParser(BaseParser):
    """Parser for plain text content."""
    
    def parse(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """Plain text needs no parsing."""
        return content, {}
    
    def reconstruct(self, text: str, metadata: Dict[str, Any]) -> str:
        """Plain text needs no reconstruction."""
        return text


class JSONParser(BaseParser):
    """Parser for JSON content."""
    
    def parse(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from JSON while preserving structure."""
        try:
            data = json.loads(content)
            texts = []
            paths = []
            self._extract_texts(data, texts, paths)
            
            return "\n".join(texts), {
                "structure": data,
                "paths": paths,
                "original_content": content
            }
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    
    def _extract_texts(self, obj: Any, texts: list, paths: list, path: str = ""):
        """Recursively extract text values from JSON."""
        if isinstance(obj, str):
            texts.append(obj)
            paths.append(path)
        elif isinstance(obj, dict):
            for key, value in obj.items():
                self._extract_texts(value, texts, paths, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                self._extract_texts(item, texts, paths, f"{path}[{i}]")
    
    def reconstruct(self, text: str, metadata: Dict[str, Any]) -> str:
        """Reconstruct JSON from sanitized text."""
        if not metadata:
            return text
        
        structure = metadata.get("structure", {})
        paths = metadata.get("paths", [])
        text_lines = text.split("\n")
        
        # Map sanitized text back to paths
        for i, (line, path) in enumerate(zip(text_lines, paths)):
            self._set_value(structure, path, line)
        
        return json.dumps(structure, ensure_ascii=False, indent=2)
    
    def _set_value(self, obj: Any, path: str, value: str):
        """Set value in nested structure using path."""
        parts = path.replace("][", ".").replace("[", ".").replace("]", "").split(".")
        current = obj
        
        for i, part in enumerate(parts[:-1]):
            if part.isdigit():
                part = int(part)
            
            if i == len(parts) - 2:
                if isinstance(current, dict):
                    current[parts[-1]] = value
                elif isinstance(current, list):
                    current[int(parts[-1])] = value
            else:
                current = current[part]


class HTMLExtractor(HTMLParser):
    """Extract text from HTML while preserving structure."""
    
    def __init__(self):
        super().__init__()
        self.texts = []
        self.current_text = []
        self.tag_stack = []
        self.tag_positions = []
    
    def handle_starttag(self, tag, attrs):
        if self.current_text:
            text = "".join(self.current_text).strip()
            if text:
                self.texts.append(text)
                self.tag_positions.append((len(self.texts) - 1, self.tag_stack.copy()))
            self.current_text = []
        self.tag_stack.append((tag, dict(attrs)))
    
    def handle_endtag(self, tag):
        if self.current_text:
            text = "".join(self.current_text).strip()
            if text:
                self.texts.append(text)
                self.tag_positions.append((len(self.texts) - 1, self.tag_stack.copy()))
            self.current_text = []
        if self.tag_stack and self.tag_stack[-1][0] == tag:
            self.tag_stack.pop()
    
    def handle_data(self, data):
        if data.strip():
            self.current_text.append(data)
    
    def get_results(self):
        # Handle any remaining text
        if self.current_text:
            text = "".join(self.current_text).strip()
            if text:
                self.texts.append(text)
                self.tag_positions.append((len(self.texts) - 1, self.tag_stack.copy()))
        
        return self.texts, self.tag_positions


class HTMLParser(BaseParser):
    """Parser for HTML content."""
    
    def parse(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from HTML while preserving structure."""
        try:
            extractor = HTMLExtractor()
            extractor.feed(content)
            texts, positions = extractor.get_results()
            
            return "\n".join(texts), {
                "original_content": content,
                "text_positions": positions
            }
        except Exception as e:
            raise ValueError(f"Invalid HTML: {e}")
    
    def reconstruct(self, text: str, metadata: Dict[str, Any]) -> str:
        """Reconstruct HTML from sanitized text."""
        if not metadata:
            return html.escape(text)
        
        # For simplicity in V1, return escaped text
        # A full implementation would rebuild the HTML structure
        return html.escape(text)