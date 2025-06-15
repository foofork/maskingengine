# MaskingEngine Architecture

MaskingEngine is designed as a modular, high-performance PII detection and masking system with a focus on privacy, extensibility, and production readiness.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    MaskingEngine Core                       │
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐ │
│  │   CLI       │    │     API      │    │   Python SDK   │ │
│  │ Interface   │    │  Interface   │    │   Interface     │ │
│  └─────────────┘    └──────────────┘    └─────────────────┘ │
│         │                   │                    │         │
│         └───────────────────┼────────────────────┘         │
│                             │                              │
│  ┌──────────────────────────┴─────────────────────────────┐ │
│  │                 Sanitizer Core                        │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │   Config    │  │   Parsers   │  │     Masker      │ │ │
│  │  │   Manager   │  │   (JSON/    │  │  (Placeholder   │ │ │
│  │  │             │  │  HTML/Text) │  │   Generation)   │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └───────────────────────────────────────────────────────┘ │
│                             │                              │
│  ┌──────────────────────────┴─────────────────────────────┐ │
│  │                Detection Engine                       │ │
│  │  ┌─────────────┐              ┌─────────────────────┐  │ │
│  │  │   Regex     │              │        NER          │  │ │
│  │  │  Detector   │              │     Detector        │  │ │
│  │  │ (Fast Mode) │              │  (DistilBERT)       │  │ │
│  │  └─────────────┘              └─────────────────────┘  │ │
│  └───────────────────────────────────────────────────────┘ │
│                             │                              │
│  ┌──────────────────────────┴─────────────────────────────┐ │
│  │              Pattern & Storage Layer                  │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │  Pattern    │  │ Rehydration │  │   Session       │ │ │
│  │  │    Pack     │  │   System    │  │   Storage       │ │ │
│  │  │   Loader    │  │             │  │                 │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Interface Layer

#### CLI Interface (`maskingengine.cli`)
- **Purpose**: Command-line access for batch processing and automation
- **Key Features**:
  - Text, JSON, and HTML processing
  - Session-based workflows
  - Stdin/stdout support for pipelines
  - Comprehensive error handling
- **Entry Point**: `maskingengine` command via setuptools

#### REST API (`maskingengine.api`)
- **Purpose**: HTTP interface for service integration
- **Technology**: FastAPI with automatic OpenAPI documentation
- **Key Features**:
  - Synchronous and session-based endpoints
  - Request/response validation with Pydantic
  - Health checks and monitoring
  - CORS support for web applications

#### Python SDK (`maskingengine`)
- **Purpose**: Direct library integration
- **Key Classes**: `Sanitizer`, `Config`, `Rehydrator`, `RehydrationPipeline`
- **Usage**: Import and use directly in Python applications

### 2. Sanitizer Core

#### Sanitizer (`maskingengine.sanitizer`)
```python
class Sanitizer:
    """Main orchestrator for PII detection and masking."""
    
    def __init__(self, config: Config = None)
    def sanitize(self, content, format=None) -> Tuple[Union[str, dict], Dict[str, str]]
```

**Responsibilities:**
- Coordinate detection pipeline
- Format detection and routing
- Deduplication of overlapping detections
- Mask map generation and management

#### Config (`maskingengine.config`)
```python
class Config:
    """Configuration management with YAML pattern integration."""
    
    def __init__(self, pattern_packs=None, whitelist=None, regex_only=False, ...)
```

**Features:**
- Dynamic pattern pack loading
- Environment-aware configuration
- Performance mode selection (regex-only vs NER+regex)
- Whitelist and validation settings

#### Parsers (`maskingengine.parsers`)
- **Text Parser**: Raw text processing with line preservation
- **JSON Parser**: Recursive object traversal with structure preservation  
- **HTML Parser**: BeautifulSoup-based parsing with tag awareness
- **Auto-detection**: Format inference from content structure

#### Masker (`maskingengine.masker`)
```python
class Masker:
    """Placeholder generation and mask map management."""
    
    def mask_detection(self, detection: Detection) -> str
    def generate_placeholder(self, pii_type: str, content: str) -> str
```

**Features:**
- Deterministic placeholder generation
- Hash-based deduplication
- Type-specific placeholder formats
- Collision-resistant hashing

### 3. Detection Engine

#### Regex Detector (`maskingengine.detectors`)
```python
class RegexDetector:
    """High-performance regex-based PII detection."""
    
    def detect(self, text: str) -> List[Detection]
```

**Features:**
- Pre-compiled pattern caching
- Multi-pattern support per PII type
- Word boundary enforcement
- Performance optimized (< 50ms typical)

#### NER Detector (`maskingengine.detectors`)
```python
class NERDetector:
    """Transformer-based named entity recognition."""
    
    def detect(self, text: str) -> List[Detection]
```

**Features:**
- DistilBERT model: `yonigo/distilbert-base-multilingual-cased-pii`
- Multilingual support
- Confidence scoring
- Contextual understanding
- Entity types: EMAIL, TEL, SOCIALNUMBER

#### Detection Coordination
- **Parallel Processing**: Regex and NER run concurrently
- **Deduplication**: Overlapping detections are merged intelligently
- **Priority System**: Regex patterns have precedence for structured data
- **Confidence Filtering**: NER results filtered by confidence threshold

### 4. Pattern & Storage Layer

#### Pattern Pack Loader (`maskingengine.pattern_packs`)
```python
class PatternPackLoader:
    """YAML-based pattern pack management."""
    
    def load_pack(self, pack_name: str) -> Optional[PatternPack]
```

**Features:**
- YAML file discovery and loading
- Pattern compilation with error handling
- Multi-language and tier support
- Runtime pattern addition

#### Rehydration System (`maskingengine.rehydrator`)
```python
class Rehydrator:
    """PII restoration from masked content."""
    
    def rehydrate(self, masked_content, mask_map: Dict[str, str]) -> str
    def validate_mask_map(self, mask_map: Dict[str, str]) -> Tuple[bool, List[str]]

class RehydrationPipeline:
    """Session-based rehydration workflows."""
    
    def sanitize_with_session(self, content, session_id: str) -> Tuple[str, str]
    def rehydrate_with_session(self, masked_content, session_id: str) -> str
```

**Features:**
- Placeholder validation and compatibility checking
- Session-based storage for AI pipeline integration
- Automatic cleanup and expiration
- Format-aware rehydration (JSON, HTML structure preservation)

## Data Flow

### 1. Sanitization Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Input     │───▶│   Format    │───▶│   Parser    │
│  Content    │    │  Detection  │    │  Selection  │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Sanitized  │◀───│   Masker    │◀───│ Detection   │
│   Output    │    │             │    │   Engine    │
└─────────────┘    └─────────────┘    └─────────────┘
        │                                     │
        │          ┌─────────────┐           │
        └─────────▶│  Mask Map   │◀──────────┘
                   │  Generation │
                   └─────────────┘
```

### 2. Detection Engine Flow

```
                    ┌─────────────┐
                    │    Text     │
                    │   Content   │
                    └─────────────┘
                            │
                    ┌───────┴───────┐
                    │               │
            ┌─────────────┐  ┌─────────────┐
            │   Regex     │  │     NER     │
            │  Detector   │  │  Detector   │
            └─────────────┘  └─────────────┘
                    │               │
                    └───────┬───────┘
                            │
                    ┌─────────────┐
                    │ Deduplication│
                    │ & Merging   │
                    └─────────────┘
                            │
                    ┌─────────────┐
                    │ Detection   │
                    │   Results   │
                    └─────────────┘
```

### 3. Pattern Pack Integration

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    YAML     │───▶│   Pattern   │───▶│  Compiled   │
│   Files     │    │    Pack     │    │   Regex     │
│  (*.yaml)   │    │   Loader    │    │  Patterns   │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
                                              ▼
                                      ┌─────────────┐
                                      │   Regex     │
                                      │  Detector   │
                                      └─────────────┘
```

## Performance Architecture

### Speed Optimization

**Regex-Only Mode (< 50ms)**:
- Pre-compiled patterns cached in memory
- Single-pass text scanning
- Minimal object allocation
- No external model loading

**NER+Regex Mode (< 200ms)**:
- Parallel processing of regex and NER
- Model loaded once and cached
- Batch processing for multiple requests
- Result deduplication optimization

### Memory Management

**Pattern Compilation**:
- Patterns compiled once at startup
- Regex objects cached and reused
- Memory-efficient pattern storage

**NER Model**:
- Model loaded on first use (lazy loading)
- Shared model instance across requests
- CPU-optimized inference (no GPU required)
- Memory-mapped model weights

**Session Storage**:
- JSON-based file storage for mask maps
- Automatic cleanup of expired sessions
- Configurable storage directory
- Memory-efficient session handling

## Security Architecture

### Privacy-First Design

**Local Processing**:
- All processing happens locally
- No network calls to external services
- No telemetry or usage tracking
- Complete data sovereignty

**Memory Safety**:
- Sensitive data not logged
- Mask maps encrypted at rest (future enhancement)
- Automatic memory cleanup
- No persistent PII storage

**Access Control**:
- Session isolation
- Configurable storage permissions
- API rate limiting ready
- Input validation and sanitization

### Data Protection

**Masking Strategy**:
- Deterministic but unpredictable placeholders
- Hash-based collision resistance
- Type-specific placeholder formats
- Reversible with proper mask map

**Rehydration Safety**:
- Mask map validation before processing
- Compatibility checking
- Session expiration and cleanup
- Audit trail capability (future enhancement)

## Extensibility Architecture

### Plugin System

**Custom Detectors**:
```python
class CustomDetector:
    def detect(self, text: str) -> List[Detection]:
        # Custom detection logic
        pass

# Register with sanitizer
sanitizer.add_detector(CustomDetector())
```

**Custom Parsers**:
```python
class CustomParser:
    def parse(self, content) -> str:
        # Custom parsing logic
        pass
    
    def reconstruct(self, text: str, original) -> Any:
        # Custom reconstruction logic
        pass
```

### Pattern Pack Ecosystem

**Community Patterns**:
- GitHub repository for community patterns
- Standardized YAML format
- Validation and testing framework
- Versioning and compatibility

**Enterprise Patterns**:
- Private pattern pack repositories
- Organization-specific PII types
- Industry-specific regulations
- Custom validation rules

## Deployment Architecture

### Container Deployment

```dockerfile
FROM python:3.11-slim

# Install MaskingEngine
RUN pip install maskingengine

# API deployment
CMD ["uvicorn", "maskingengine.api.main:app", "--host", "0.0.0.0"]
```

### Microservice Integration

```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: maskingengine
spec:
  replicas: 3
  selector:
    matchLabels:
      app: maskingengine
  template:
    spec:
      containers:
      - name: maskingengine
        image: maskingengine:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Scaling Considerations

**Horizontal Scaling**:
- Stateless API design
- Shared pattern pack storage
- Load balancer compatible
- No session affinity required

**Vertical Scaling**:
- CPU-bound workloads
- Memory usage scales with content size
- NER model fits in 256MB RAM
- Pattern compilation overhead minimal

## Testing Architecture

### Unit Testing
- Component isolation
- Mock external dependencies
- Pattern-specific test cases
- Performance benchmarking

### Integration Testing
- End-to-end workflow testing
- API contract validation
- Cross-format compatibility
- Session lifecycle testing

### Performance Testing
- Throughput benchmarking
- Memory usage profiling
- Latency measurement
- Stress testing with large content

### Security Testing
- Input validation testing
- Injection attack prevention
- Memory safety verification
- Access control validation

## Monitoring and Observability

### Metrics (Future Enhancement)
- Detection accuracy rates
- Processing latencies
- Memory usage patterns
- Error rates and types

### Logging
- Structured JSON logging
- Configurable log levels
- Error tracking and alerting
- Performance monitoring

### Health Checks
- Component status monitoring
- Pattern pack validation
- Model availability checks
- Storage system health

This architecture provides a solid foundation for scalable, secure, and maintainable PII detection and masking operations while maintaining the flexibility to adapt to diverse use cases and deployment environments.