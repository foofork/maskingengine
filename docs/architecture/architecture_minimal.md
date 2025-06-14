# Minimal Architecture Design - Local-First PII Sanitizer

## 1. Core Architecture Overview

### 1.1 Design Principles
- **Simplicity First**: No reversible masking, no async, no streaming
- **Performance Focus**: <100ms latency target
- **Synchronous Only**: All operations are blocking
- **Minimal Dependencies**: Reduce external library usage
- **5 Core Modules**: Config, Parser, Detector, Masker, Sanitizer

### 1.2 Data Flow
```
Input (text/JSON/HTML) 
    → Config
    → Parser (format detection & extraction)
    → Detector (regex + NER in sequence)
    → Masker (simple <<TYPE_HASH>> replacement)
    → Output
```

## 2. Core Modules

### 2.1 Module Structure
```
maskingengine/
├── config.py       # Configuration and patterns
├── parsers.py      # Format parsers (text/JSON/HTML)
├── detectors.py    # PII detection (regex + NER)
├── masker.py       # Simple placeholder replacement
└── sanitizer.py    # Main orchestrator
```

### 2.2 Module Responsibilities

#### Config Module
- Load and validate configuration
- Store regex patterns
- Define PII types and placeholders
- No external config files - all in-code

#### Parser Module
- Auto-detect format (text/JSON/HTML)
- Extract text content with position tracking
- Preserve structure for reconstruction
- Single-pass parsing

#### Detector Module
- Run regex patterns first (fast path)
- Run NER model second (if enabled)
- Merge detections without conflicts
- Return positions and types

#### Masker Module
- Generate deterministic hash for each PII type
- Replace with <<TYPE_HASH>> format
- Apply replacements in reverse order
- No state, no tokens

#### Sanitizer Module
- Orchestrate the pipeline
- Handle errors gracefully
- Provide simple API surface
- Measure performance

## 3. Detailed Component Design

### 3.1 Config Component
```python
# config.py
class Config:
    # Regex patterns defined inline
    PATTERNS = {
        'EMAIL': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'PHONE_US': r'(?:\+1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
        'SSN': r'\b\d{3}-\d{2}-\d{4}\b',
        'CREDIT_CARD': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
    }
    
    # Simple type mapping
    TYPE_HASHES = {
        'EMAIL': '7A9B2C',
        'PHONE': '4D8E1F',
        'SSN': '6C3A9D',
        'CREDIT_CARD': '2F7B8E',
        'PERSON': '9E4C6A',
        'ORGANIZATION': '1B8D3F',
        'LOCATION': '5A2E9C'
    }
    
    # Performance settings
    MAX_TEXT_LENGTH = 1_000_000  # 1MB
    NER_ENABLED = True
    NER_MODEL_PATH = "models/en_core_web_sm"
```

### 3.2 Parser Component
```python
# parsers.py
class Parser:
    @staticmethod
    def parse(input_data):
        # Auto-detect format
        if isinstance(input_data, dict):
            return JSONParser.parse(input_data)
        elif '<' in str(input_data)[:100]:  # Quick HTML check
            return HTMLParser.parse(input_data)
        else:
            return TextParser.parse(input_data)

class TextParser:
    @staticmethod
    def parse(text):
        return [{
            'text': text,
            'offset': 0,
            'type': 'text'
        }]

class JSONParser:
    @staticmethod
    def parse(data):
        chunks = []
        _extract_values(data, chunks, [])
        return chunks
    
    @staticmethod
    def reconstruct(original, chunks, replacements):
        result = copy.deepcopy(original)
        for chunk, replacement in zip(chunks, replacements):
            _set_by_path(result, chunk['path'], replacement)
        return result

class HTMLParser:
    @staticmethod
    def parse(html):
        # Use simple regex for minimal parsing
        text_pattern = r'>([^<]+)<'
        chunks = []
        for match in re.finditer(text_pattern, html):
            chunks.append({
                'text': match.group(1),
                'offset': match.start(1),
                'type': 'html'
            })
        return chunks
```

### 3.3 Detector Component
```python
# detectors.py
import re
from typing import List, NamedTuple

class Detection(NamedTuple):
    type: str
    start: int
    end: int
    text: str

class RegexDetector:
    def __init__(self, patterns):
        self.compiled = {
            name: re.compile(pattern) 
            for name, pattern in patterns.items()
        }
    
    def detect(self, text: str) -> List[Detection]:
        detections = []
        for pii_type, pattern in self.compiled.items():
            for match in pattern.finditer(text):
                detections.append(Detection(
                    type=pii_type,
                    start=match.start(),
                    end=match.end(),
                    text=match.group()
                ))
        return detections

class NERDetector:
    def __init__(self, model_path):
        # Lazy load model only if needed
        self.model = None
        self.model_path = model_path
    
    def detect(self, text: str) -> List[Detection]:
        if not self.model:
            import spacy
            self.model = spacy.load(self.model_path)
        
        doc = self.model(text)
        detections = []
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'GPE']:
                detections.append(Detection(
                    type=ent.label_,
                    start=ent.start_char,
                    end=ent.end_char,
                    text=ent.text
                ))
        return detections

class Detector:
    def __init__(self, config):
        self.regex_detector = RegexDetector(config.PATTERNS)
        self.ner_detector = NERDetector(config.NER_MODEL_PATH) if config.NER_ENABLED else None
    
    def detect_all(self, text: str) -> List[Detection]:
        # Regex first (fast)
        detections = self.regex_detector.detect(text)
        
        # NER second (slower)
        if self.ner_detector:
            ner_detections = self.ner_detector.detect(text)
            detections.extend(ner_detections)
        
        # Simple deduplication by position
        return self._deduplicate(detections)
    
    def _deduplicate(self, detections):
        # Sort by start position
        sorted_detections = sorted(detections, key=lambda d: (d.start, -d.end))
        
        # Remove overlaps
        result = []
        last_end = -1
        for detection in sorted_detections:
            if detection.start >= last_end:
                result.append(detection)
                last_end = detection.end
        
        return result
```

### 3.4 Masker Component
```python
# masker.py
class Masker:
    def __init__(self, type_hashes):
        self.type_hashes = type_hashes
    
    def mask(self, text: str, detections: List[Detection]) -> str:
        # Sort detections in reverse order
        sorted_detections = sorted(detections, key=lambda d: d.start, reverse=True)
        
        # Apply masks from end to beginning
        result = text
        for detection in sorted_detections:
            placeholder = self._get_placeholder(detection.type)
            result = result[:detection.start] + placeholder + result[detection.end:]
        
        return result
    
    def _get_placeholder(self, pii_type: str) -> str:
        # Normalize type mapping
        type_map = {
            'PERSON': 'PERSON',
            'ORG': 'ORGANIZATION', 
            'GPE': 'LOCATION'
        }
        
        normalized_type = type_map.get(pii_type, pii_type)
        hash_value = self.type_hashes.get(normalized_type, 'XXXXXX')
        return f"<<{normalized_type}_{hash_value}>>"
```

### 3.5 Sanitizer Component
```python
# sanitizer.py
import time
from typing import Union, Dict, Any

class Sanitizer:
    def __init__(self, config=None):
        self.config = config or Config()
        self.detector = Detector(self.config)
        self.masker = Masker(self.config.TYPE_HASHES)
    
    def sanitize(self, input_data: Union[str, Dict, Any]) -> Union[str, Dict]:
        start_time = time.time()
        
        try:
            # Parse input
            chunks = Parser.parse(input_data)
            
            # Process each chunk
            results = []
            for chunk in chunks:
                # Detect PII
                detections = self.detector.detect_all(chunk['text'])
                
                # Apply masking
                masked_text = self.masker.mask(chunk['text'], detections)
                results.append(masked_text)
            
            # Reconstruct output
            if isinstance(input_data, dict):
                return JSONParser.reconstruct(input_data, chunks, results)
            elif chunks and chunks[0]['type'] == 'html':
                return self._reconstruct_html(input_data, chunks, results)
            else:
                return results[0] if results else ""
                
        finally:
            elapsed = (time.time() - start_time) * 1000
            if elapsed > 100:
                print(f"Warning: Processing took {elapsed:.1f}ms")
    
    def _reconstruct_html(self, original, chunks, results):
        # Simple HTML reconstruction
        result = original
        for chunk, masked in zip(reversed(chunks), reversed(results)):
            result = (result[:chunk['offset']] + 
                     masked + 
                     result[chunk['offset'] + len(chunk['text']):])
        return result
```

## 4. Performance Optimization Strategies

### 4.1 Regex Optimization
- **Pre-compile all patterns**: Done at initialization
- **Use non-capturing groups**: Reduce memory overhead
- **Order patterns by frequency**: Email/phone first
- **Limit backtracking**: Use possessive quantifiers

### 4.2 NER Optimization
- **Lazy loading**: Load model only when needed
- **Batch processing**: Process multiple chunks together
- **Model selection**: Use smallest model that works
- **Disable unused components**: Only NER pipeline

### 4.3 General Optimizations
- **Early termination**: Skip NER if regex finds enough
- **Length limits**: Reject documents >1MB
- **String operations**: Use slicing instead of regex where possible
- **Memory reuse**: Avoid creating intermediate strings

### 4.4 Performance Benchmarks
```python
# Target performance metrics
PERFORMANCE_TARGETS = {
    '1KB_document': 10,    # 10ms
    '10KB_document': 50,   # 50ms
    '100KB_document': 100, # 100ms
    'memory_usage': 50,    # 50MB max
}
```

## 5. API Design

### 5.1 Python Library API
```python
# Simple, synchronous API
from maskingengine import Sanitizer

# Basic usage
sanitizer = Sanitizer()
result = sanitizer.sanitize("John's email is john@example.com")
# Output: "<<PERSON_9E4C6A>>'s email is <<EMAIL_7A9B2C>>"

# JSON sanitization
data = {"user": {"name": "John Doe", "email": "john@example.com"}}
result = sanitizer.sanitize(data)
# Output: {"user": {"name": "<<PERSON_9E4C6A>>", "email": "<<EMAIL_7A9B2C>>"}}
```

### 5.2 REST API (FastAPI)
```python
# Minimal endpoints
POST /sanitize
    Request: {"content": "text or JSON", "format": "auto|text|json|html"}
    Response: {"sanitized": "...", "processing_time_ms": 45}

GET /health
    Response: {"status": "ok", "version": "1.0.0"}
```

### 5.3 CLI Interface
```bash
# Stdin/stdout processing
echo "John's SSN is 123-45-6789" | maskingengine

# File processing
maskingengine -i input.txt -o output.txt

# JSON processing
maskingengine -f json < data.json > sanitized.json
```

## 6. Error Handling Strategy

### 6.1 Graceful Degradation
- If NER fails → use regex only
- If parsing fails → treat as plain text
- If timeout → return partial results
- Never throw exceptions to user

### 6.2 Performance Boundaries
- Document size >1MB → reject with error
- Processing time >200ms → log warning
- Memory usage >100MB → garbage collect
- Malformed input → fallback to text

## 7. Testing Strategy

### 7.1 Unit Tests
- Test each detector independently
- Test parser format detection
- Test masker replacements
- Test config validation

### 7.2 Integration Tests
- End-to-end text sanitization
- JSON structure preservation
- HTML tag preservation
- Performance under 100ms

### 7.3 Performance Tests
- Measure latency distribution
- Test with various document sizes
- Verify memory usage
- Stress test with concurrent requests

## 8. Deployment Architecture

### 8.1 Package Structure
```
maskingengine/
├── __init__.py
├── config.py
├── parsers.py
├── detectors.py
├── masker.py
├── sanitizer.py
├── api.py          # FastAPI app
├── cli.py          # Click CLI
└── models/         # Pre-trained NER model
```

### 8.2 Distribution
- **PyPI Package**: `pip install maskingengine`
- **Docker Image**: For API deployment
- **Binary**: PyInstaller for CLI distribution
- **Models**: Bundled or downloaded on first use

## 9. Future Considerations (Out of Scope)

- Streaming support for large files
- Async API for better concurrency  
- Reversible masking with tokens
- Custom detector plugins
- Multi-language support
- GPU acceleration

## 10. Success Metrics

### 10.1 Performance
- P50 latency: <50ms
- P95 latency: <100ms
- P99 latency: <150ms
- Throughput: >100 docs/sec

### 10.2 Accuracy
- Regex precision: >95%
- NER recall: >85%
- False positive rate: <5%
- Zero false negatives for SSN/Credit Cards

### 10.3 Simplicity
- Total LOC: <1000
- Dependencies: <5
- Setup time: <1 minute
- API methods: <5