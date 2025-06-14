# API Contracts and Data Flow Specifications

## 1. Core Data Types

### 1.1 Input/Output Types
```python
# Type definitions
InputType = Union[str, Dict[str, Any]]
OutputType = Union[str, Dict[str, Any]]

# Detection result
Detection = NamedTuple('Detection', [
    ('type', str),        # PII type (EMAIL, PHONE, etc.)
    ('start', int),       # Start position in text
    ('end', int),         # End position in text  
    ('text', str)         # Original text (internal use only)
])

# Text chunk for processing
TextChunk = Dict[str, Any]  # {text: str, offset: int, type: str, path?: List}
```

### 1.2 Configuration Contract
```python
class Config:
    """Immutable configuration - all settings defined at init"""
    
    # Required patterns (no external config)
    PATTERNS: Dict[str, str]
    
    # Required type mappings  
    TYPE_HASHES: Dict[str, str]
    
    # Performance limits
    MAX_TEXT_LENGTH: int = 1_000_000
    
    # Feature flags
    NER_ENABLED: bool = True
    NER_MODEL_PATH: str = "models/en_core_web_sm"
```

## 2. Module Interfaces

### 2.1 Parser Interface
```python
class Parser:
    @staticmethod
    def parse(input_data: InputType) -> List[TextChunk]:
        """
        Extract text chunks from input data
        
        Args:
            input_data: Text string, dict (JSON), or HTML string
            
        Returns:
            List of chunks with text and metadata
            
        Guarantees:
            - Never raises exceptions
            - Always returns list (empty if error)
            - Preserves input structure metadata
        """

class JSONParser:
    @staticmethod  
    def reconstruct(original: dict, 
                   chunks: List[TextChunk], 
                   replacements: List[str]) -> dict:
        """
        Rebuild JSON with sanitized values
        
        Args:
            original: Original JSON data
            chunks: Extracted chunks with paths
            replacements: Sanitized text for each chunk
            
        Returns:
            New dict with sanitized values
            
        Guarantees:
            - Preserves JSON structure exactly
            - Only modifies string values
            - Deep copy prevents mutations
        """
```

### 2.2 Detector Interface
```python
class Detector:
    def detect_all(self, text: str) -> List[Detection]:
        """
        Detect all PII in text using regex + NER
        
        Args:
            text: Input text to scan
            
        Returns:
            Deduplicated list of detections
            
        Guarantees:
            - No overlapping detections
            - Sorted by position
            - Regex runs first (fast path)
            - NER optional (graceful skip)
        """

class RegexDetector:
    def detect(self, text: str) -> List[Detection]:
        """
        Fast regex-based detection
        
        Performance: O(n*p) where n=text length, p=patterns
        Memory: O(m) where m=number of matches
        """

class NERDetector:  
    def detect(self, text: str) -> List[Detection]:
        """
        ML-based entity detection
        
        Performance: O(n) with model loaded
        Memory: ~40MB for model + O(n) for processing
        First call loads model (lazy)
        """
```

### 2.3 Masker Interface
```python
class Masker:
    def mask(self, text: str, detections: List[Detection]) -> str:
        """
        Replace detected PII with placeholders
        
        Args:
            text: Original text
            detections: PII locations to mask
            
        Returns:
            Text with <<TYPE_HASH>> placeholders
            
        Guarantees:
            - Deterministic output
            - No position conflicts  
            - Applied right-to-left
            - Type normalization (PERSON/ORG/GPE)
        """
```

### 2.4 Sanitizer Interface (Main API)
```python
class Sanitizer:
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize with optional config
        
        Defaults used if config not provided
        Components initialized synchronously
        """
    
    def sanitize(self, input_data: InputType) -> OutputType:
        """
        Main sanitization method
        
        Args:
            input_data: Text, JSON dict, or HTML string
            
        Returns:
            Same type as input with PII masked
            
        Guarantees:
            - Type preservation (str→str, dict→dict)
            - <100ms for documents <100KB
            - Never raises exceptions
            - Graceful degradation on errors
            
        Performance:
            - Text: O(n) where n = length
            - JSON: O(n*d) where d = depth  
            - HTML: O(n*t) where t = tags
        """
```

## 3. REST API Contract

### 3.1 Endpoints
```yaml
POST /sanitize:
  description: Sanitize a single document
  request:
    content-type: application/json
    schema:
      type: object
      required: [content]
      properties:
        content:
          type: [string, object]
          description: Text or JSON to sanitize
        format:
          type: string
          enum: [auto, text, json, html]
          default: auto
          description: Input format hint
  response:
    content-type: application/json
    schema:
      type: object
      properties:
        sanitized:
          type: [string, object]
          description: Sanitized content (same type as input)
        processing_time_ms:
          type: number
          description: Processing time in milliseconds
  errors:
    400: Invalid request format
    413: Input too large (>1MB)
    500: Internal processing error

GET /health:
  description: Health check
  response:
    schema:
      type: object
      properties:
        status:
          type: string
          enum: [ok, degraded]
        version:
          type: string
        model_loaded:
          type: boolean
```

### 3.2 Example Requests/Responses
```json
// Text sanitization
POST /sanitize
{
  "content": "Email John at john@example.com"
}
Response:
{
  "sanitized": "Email <<PERSON_9E4C6A>> at <<EMAIL_7A9B2C>>",
  "processing_time_ms": 23.5
}

// JSON sanitization  
POST /sanitize
{
  "content": {
    "user": {
      "name": "Jane Doe",
      "contact": "jane@example.com"
    }
  },
  "format": "json"
}
Response:
{
  "sanitized": {
    "user": {
      "name": "<<PERSON_9E4C6A>>",
      "contact": "<<EMAIL_7A9B2C>>"
    }
  },
  "processing_time_ms": 31.2
}
```

## 4. CLI Contract

### 4.1 Command Structure
```bash
maskingengine [OPTIONS] [INPUT]

Options:
  -i, --input FILE     Input file (default: stdin)
  -o, --output FILE    Output file (default: stdout)
  -f, --format FORMAT  Format: auto|text|json|html (default: auto)
  -h, --help          Show help
  -v, --version       Show version

Exit codes:
  0: Success
  1: General error
  2: Invalid arguments
  3: Input too large
```

### 4.2 Usage Examples
```bash
# Pipe usage
$ echo "Call me at 555-1234" | maskingengine
Call me at <<PHONE_4D8E1F>>

# File processing
$ maskingengine -i personal.txt -o sanitized.txt
$ echo $?
0

# JSON with explicit format
$ maskingengine -f json < data.json > clean.json

# Error handling
$ maskingengine -i 2GB_file.txt
Error: Input exceeds maximum size (1MB)
$ echo $?
3
```

## 5. Python Library Contract

### 5.1 Public API
```python
# maskingengine/__init__.py
from .sanitizer import Sanitizer
from .config import Config

__all__ = ['Sanitizer', 'Config']
__version__ = '1.0.0'
```

### 5.2 Usage Examples
```python
from maskingengine import Sanitizer

# Basic usage - all defaults
sanitizer = Sanitizer()
result = sanitizer.sanitize("My SSN is 123-45-6789")
assert result == "My SSN is <<SSN_6C3A9D>>"

# JSON sanitization
data = {"email": "test@example.com", "phone": "555-0123"}
result = sanitizer.sanitize(data)
assert result == {"email": "<<EMAIL_7A9B2C>>", "phone": "<<PHONE_4D8E1F>>"}

# Custom config
from maskingengine import Config
config = Config()
config.NER_ENABLED = False  # Regex only
sanitizer = Sanitizer(config)

# Error handling built-in
result = sanitizer.sanitize(None)  # Returns empty string
result = sanitizer.sanitize({"bad": object()})  # Treats as text
```

## 6. Performance Contracts

### 6.1 Latency SLA
```python
# Performance guarantees by input size
LATENCY_SLA = {
    "1KB": 10,    # 10ms max
    "10KB": 50,   # 50ms max  
    "100KB": 100, # 100ms max
    "1MB": None,  # Best effort
}

# Measurement points
TIMING_POINTS = [
    "parse_start",
    "parse_end",
    "detect_start", 
    "detect_end",
    "mask_start",
    "mask_end",
    "total"
]
```

### 6.2 Resource Limits
```python
# Hard limits
MAX_DOCUMENT_SIZE = 1_000_000  # 1MB
MAX_MEMORY_USAGE = 100_000_000  # 100MB
MAX_PROCESSING_TIME = 1000  # 1 second timeout

# Soft limits (warnings)
WARN_DOCUMENT_SIZE = 100_000  # 100KB
WARN_PROCESSING_TIME = 100  # 100ms
```

## 7. Error Handling Contract

### 7.1 Error Strategy
```python
# Never throw exceptions to user
# Always return best-effort result
# Log errors for debugging

def safe_operation(func, fallback):
    try:
        return func()
    except Exception as e:
        log.warning(f"Operation failed: {e}")
        return fallback

# Example usage in sanitizer
def sanitize(self, input_data):
    # Parse with fallback
    chunks = safe_operation(
        lambda: Parser.parse(input_data),
        fallback=[TextChunk(text=str(input_data), offset=0)]
    )
    
    # Detect with fallback  
    for chunk in chunks:
        detections = safe_operation(
            lambda: self.detector.detect_all(chunk['text']),
            fallback=[]
        )
        # Continue processing...
```

### 7.2 Degradation Modes
```
1. NER fails → Use regex only
2. Parser fails → Treat as plain text
3. Timeout → Return partial results
4. Memory limit → Reject input
5. Unknown error → Log and continue
```

## 8. Threading Contract

### 8.1 Thread Safety
```python
# Sanitizer is thread-safe for concurrent calls
# No shared mutable state between calls
# Model loading is synchronized (lazy init)

# Safe concurrent usage
import concurrent.futures

sanitizer = Sanitizer()  # Create once

with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [
        executor.submit(sanitizer.sanitize, doc) 
        for doc in documents
    ]
    results = [f.result() for f in futures]
```

### 8.2 No Async Support
```python
# All operations are synchronous
# No async/await methods
# Use threading for concurrency
# FastAPI handles async wrapping for API
```

## 9. Extensibility Contract

### 9.1 Closed for Extension
```python
# No plugin system
# No custom detectors
# No format extensions
# Configuration is minimal

# This is intentional for:
# - Simplicity
# - Performance  
# - Security
# - Predictability
```

### 9.2 Future Compatibility
```python
# Version 1.x guarantees:
# - Same input/output format
# - Same placeholder format
# - Backward compatible API
# - No breaking changes

# Version 2.x may add:
# - New detection types
# - New formats
# - Async support
# - Plugin system
```