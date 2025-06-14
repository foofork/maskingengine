# Phase 3: Modular Architecture Design

## 1. Module Structure

```
maskingengine/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── sanitizer.py         # Main Sanitizer class
│   ├── config.py            # Configuration management
│   ├── types.py             # Type definitions
│   └── exceptions.py        # Custom exceptions
├── detectors/
│   ├── __init__.py
│   ├── base.py              # Base detector interface
│   ├── regex_detector.py    # Regex-based detection
│   ├── ner_detector.py      # NER model detection
│   ├── patterns.py          # Pattern definitions
│   └── merger.py            # Detection merging logic
├── maskers/
│   ├── __init__.py
│   ├── base.py              # Base masker interface
│   ├── simple_masker.py     # Basic masking
│   ├── reversible_masker.py # Token-based reversible masking
│   └── strategies.py        # Masking strategies
├── parsers/
│   ├── __init__.py
│   ├── base.py              # Base parser interface
│   ├── text_parser.py       # Plain text parsing
│   ├── json_parser.py       # JSON parsing
│   ├── html_parser.py       # HTML parsing
│   └── format_detector.py   # Auto format detection
├── models/
│   ├── __init__.py
│   ├── ner_model.py         # Lightweight NER model wrapper
│   └── model_loader.py      # Model loading utilities
├── api/
│   ├── __init__.py
│   ├── app.py               # FastAPI application
│   ├── routes.py            # API endpoints
│   ├── models.py            # Pydantic models
│   └── middleware.py        # Request/response middleware
├── cli/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── commands.py          # CLI commands
│   └── utils.py             # CLI utilities
└── utils/
    ├── __init__.py
    ├── performance.py       # Performance utilities
    ├── validation.py        # Input validation
    └── logging.py           # Logging configuration
```

## 2. Module Interfaces

### 2.1 Core Module
```python
# core/types.py
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class PIIType(Enum):
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"

@dataclass
class Detection:
    type: PIIType
    start: int
    end: int
    text: str
    confidence: float
    method: str  # 'regex' or 'ner'
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class TextChunk:
    text: str
    offset: int = 0
    metadata: Optional[Dict[str, Any]] = None

# core/sanitizer.py
class Sanitizer:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._init_components()
    
    def sanitize(self, 
                input_data: Union[str, dict, bytes],
                format: Optional[str] = None) -> Union[str, dict]:
        """Main sanitization interface"""
        pass
    
    def sanitize_text(self, text: str) -> str:
        """Direct text sanitization"""
        pass
    
    def detect_pii(self, text: str) -> List[Detection]:
        """Detection-only interface"""
        pass
```

### 2.2 Detector Module
```python
# detectors/base.py
from abc import ABC, abstractmethod
from typing import List

class BaseDetector(ABC):
    @abstractmethod
    def detect(self, text: str) -> List[Detection]:
        """Detect PII in text"""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate detector configuration"""
        pass

# detectors/regex_detector.py
class RegexDetector(BaseDetector):
    def __init__(self, patterns: Optional[Dict[str, Pattern]] = None):
        self.patterns = patterns or default_patterns()
        self._compile_patterns()
    
    def detect(self, text: str) -> List[Detection]:
        """Implement regex detection"""
        pass
    
    def add_pattern(self, name: str, pattern: Pattern) -> None:
        """Add custom pattern"""
        pass

# detectors/ner_detector.py  
class NERDetector(BaseDetector):
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or get_default_model_path()
        self._load_model()
    
    def detect(self, text: str) -> List[Detection]:
        """Implement NER detection"""
        pass
    
    def update_model(self, model_path: str) -> None:
        """Update NER model"""
        pass
```

### 2.3 Parser Module
```python
# parsers/base.py
from abc import ABC, abstractmethod
from typing import List, Any, Union

class BaseParser(ABC):
    @abstractmethod
    def parse(self, input_data: Union[str, bytes, dict]) -> List[TextChunk]:
        """Parse input into text chunks"""
        pass
    
    @abstractmethod
    def reconstruct(self, chunks: List[TextChunk], 
                   masked_texts: List[str]) -> Any:
        """Reconstruct output from masked chunks"""
        pass

# parsers/json_parser.py
class JSONParser(BaseParser):
    def parse(self, json_data: Union[str, dict]) -> List[TextChunk]:
        """Parse JSON and extract text chunks"""
        pass
    
    def reconstruct(self, chunks: List[TextChunk], 
                   masked_texts: List[str]) -> dict:
        """Reconstruct JSON with masked values"""
        pass

# parsers/html_parser.py
class HTMLParser(BaseParser):
    def parse(self, html_data: str) -> List[TextChunk]:
        """Parse HTML and extract text chunks"""
        pass
    
    def reconstruct(self, chunks: List[TextChunk], 
                   masked_texts: List[str]) -> str:
        """Reconstruct HTML with masked values"""
        pass
```

### 2.4 Masker Module
```python
# maskers/base.py
from abc import ABC, abstractmethod
from typing import List, Optional

class BaseMasker(ABC):
    @abstractmethod
    def mask(self, text: str, detections: List[Detection]) -> str:
        """Apply masks to text"""
        pass
    
    @abstractmethod
    def unmask(self, masked_text: str) -> Optional[str]:
        """Reverse masking if supported"""
        pass

# maskers/simple_masker.py
class SimpleMasker(BaseMasker):
    def __init__(self, format: MaskFormat = MaskFormat.TYPE_AWARE):
        self.format = format
    
    def mask(self, text: str, detections: List[Detection]) -> str:
        """Apply simple masks"""
        pass

# maskers/reversible_masker.py
class ReversibleMasker(BaseMasker):
    def __init__(self):
        self.token_map = {}
        self.token_generator = TokenGenerator()
    
    def mask(self, text: str, detections: List[Detection]) -> str:
        """Apply reversible masks with tokens"""
        pass
    
    def unmask(self, masked_text: str) -> str:
        """Restore original text from tokens"""
        pass
```

## 3. API Module Design

### 3.1 FastAPI Application
```python
# api/models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class SanitizeRequest(BaseModel):
    content: Union[str, dict]
    format: Optional[str] = Field(None, description="Input format")
    options: Optional[Dict[str, Any]] = None

class SanitizeResponse(BaseModel):
    sanitized: Union[str, dict]
    detections: List[DetectionResult]
    metadata: ResponseMetadata

class BatchRequest(BaseModel):
    documents: List[SanitizeRequest]
    parallel: bool = True

# api/routes.py
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.post("/sanitize")
async def sanitize(request: SanitizeRequest) -> SanitizeResponse:
    """Single document sanitization"""
    pass

@router.post("/sanitize/batch")
async def sanitize_batch(request: BatchRequest) -> List[SanitizeResponse]:
    """Batch sanitization"""
    pass

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": __version__}
```

### 3.2 CLI Module
```python
# cli/main.py
import click
from typing import Optional

@click.group()
@click.version_option()
def cli():
    """MaskingEngine CLI - Local-first PII sanitizer"""
    pass

@cli.command()
@click.argument('input_file', type=click.File('r'), default='-')
@click.option('--output', '-o', type=click.File('w'), default='-')
@click.option('--format', '-f', type=click.Choice(['auto', 'text', 'json', 'html']))
@click.option('--config', '-c', type=click.Path(exists=True))
def sanitize(input_file, output, format, config):
    """Sanitize a file or stdin"""
    pass

@cli.command()
@click.option('--host', default='127.0.0.1')
@click.option('--port', default=8000)
def serve(host, port):
    """Start the REST API server"""
    pass
```

## 4. Configuration Module

### 4.1 Configuration Schema
```python
# core/config.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class DetectorConfig(BaseModel):
    regex_enabled: bool = True
    ner_enabled: bool = True
    custom_patterns: Optional[Dict[str, str]] = None
    confidence_threshold: float = 0.7

class MaskerConfig(BaseModel):
    type: str = "type_aware"  # type_aware, length_preserving, fixed
    reversible: bool = False
    placeholder_format: str = "[{type}]"

class PerformanceConfig(BaseModel):
    max_document_size: int = 10_000_000  # 10MB
    timeout_ms: int = 100
    batch_size: int = 100
    cache_enabled: bool = True
    cache_size: int = 1000

class Config(BaseModel):
    detectors: DetectorConfig = Field(default_factory=DetectorConfig)
    masker: MaskerConfig = Field(default_factory=MaskerConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    logging_enabled: bool = False
    
    @classmethod
    def from_file(cls, path: str) -> 'Config':
        """Load config from JSON/YAML file"""
        pass
```

## 5. Integration Points

### 5.1 Python Library Usage
```python
from maskingengine import Sanitizer, Config

# Basic usage
sanitizer = Sanitizer()
result = sanitizer.sanitize("John Doe's email is john@example.com")

# Advanced usage with config
config = Config(
    detectors=DetectorConfig(confidence_threshold=0.9),
    masker=MaskerConfig(reversible=True)
)
sanitizer = Sanitizer(config)

# Direct detection
detections = sanitizer.detect_pii("Call me at 555-123-4567")

# Batch processing
results = sanitizer.sanitize_batch(documents)
```

### 5.2 REST API Usage
```bash
# Single document
curl -X POST http://localhost:8000/sanitize \
  -H "Content-Type: application/json" \
  -d '{"content": "Email: john@example.com"}'

# Batch processing
curl -X POST http://localhost:8000/sanitize/batch \
  -H "Content-Type: application/json" \
  -d '{"documents": [{"content": "..."}, {"content": "..."}]}'
```

### 5.3 CLI Usage
```bash
# Pipe usage
echo "John's SSN is 123-45-6789" | maskingengine sanitize

# File processing
maskingengine sanitize input.txt -o output.txt

# JSON processing
maskingengine sanitize data.json --format json

# Start API server
maskingengine serve --port 8080
```

## 6. Extension Points

### 6.1 Plugin Architecture
```python
# Future extension for custom detectors
class DetectorPlugin(ABC):
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def detect(self, text: str) -> List[Detection]:
        pass

# Registration
sanitizer.register_detector(CustomDetector())
```

### 6.2 Output Formats
```python
# Future extension for additional formats
class OutputFormatter(ABC):
    @abstractmethod
    def format(self, result: SanitizationResult) -> Any:
        pass

# Implementations
class XMLFormatter(OutputFormatter):
    pass

class CSVFormatter(OutputFormatter):
    pass
```