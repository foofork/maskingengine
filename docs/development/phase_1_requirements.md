# Phase 1: Requirements Analysis - Local-First PII Sanitizer

## 1. Core Functional Requirements

### 1.1 Dual Detection System
- **Regex Pattern Detection**
  - Pre-defined patterns for common PII types
  - Configurable pattern library
  - Pattern validation and testing
  - Custom pattern support
  
- **NER Model Detection**
  - Named Entity Recognition for contextual detection
  - Support for persons, organizations, locations
  - Model should be lightweight and fast
  - Fallback to regex when NER confidence is low

### 1.2 Masking Capabilities
- **Placeholder Masking**
  - Type-aware placeholders (e.g., [EMAIL], [PHONE], [SSN])
  - Consistent masking within documents
  - Reversible masking with secure token mapping (optional)
  - Length-preserving masks for certain types

### 1.3 Format Support
- **Plain Text**
  - UTF-8 encoding support
  - Line-by-line processing
  - Preserve formatting and whitespace
  
- **JSON**
  - Parse and traverse JSON structures
  - Mask values while preserving structure
  - Handle nested objects and arrays
  - Support for JSON streaming
  
- **HTML**
  - Parse HTML safely
  - Mask text content while preserving markup
  - Handle attributes containing PII
  - Preserve document structure

## 2. Interface Requirements

### 2.1 Python Library
- Simple import: `from maskingengine import Sanitizer`
- Synchronous and asynchronous APIs
- Context manager support
- Type hints and documentation
- Pip-installable package

### 2.2 REST API
- FastAPI-based implementation
- OpenAPI/Swagger documentation
- JSON request/response format
- Batch processing endpoint
- Health check endpoint
- No authentication (local-first)

### 2.3 CLI Tool
- Single binary distribution
- Pipe-friendly for Unix workflows
- File and stdin/stdout support
- Progress indicators for large files
- Configuration file support

## 3. Non-Functional Requirements

### 3.1 Performance
- **Latency**: <100ms for typical documents (1-10KB)
- **Throughput**: Process at least 100 documents/second
- **Memory**: <100MB base memory footprint
- **Startup**: <1 second cold start

### 3.2 Privacy & Security
- **Zero Telemetry**: No data collection, analytics, or phone-home
- **Local-Only**: All processing happens on-device
- **No Network**: Can operate completely offline
- **Secure Defaults**: Conservative detection thresholds

### 3.3 Reliability
- **Graceful Degradation**: Continue with partial results on errors
- **Input Validation**: Handle malformed inputs safely
- **Resource Limits**: Prevent DoS from large inputs
- **Logging**: Optional local logging for debugging

## 4. Edge Cases & Constraints

### 4.1 Detection Edge Cases
- International formats (phone numbers, addresses)
- Ambiguous text (e.g., "John" as name vs. common word)
- Mixed languages in single document
- PII in URLs, file paths, or code
- Partial or malformed PII

### 4.2 Format Edge Cases
- Invalid JSON/HTML
- Binary data in text streams
- Very large documents (>10MB)
- Streaming data requirements
- Character encoding issues

### 4.3 System Constraints
- Must work on Linux, macOS, Windows
- Python 3.8+ compatibility
- Minimal dependencies
- No GPU requirement
- Single-threaded performance target

## 5. Success Criteria

### 5.1 Accuracy Metrics
- 95%+ precision for common PII types
- 90%+ recall for regex-detectable patterns
- False positive rate <5%
- Configurable sensitivity levels

### 5.2 Performance Metrics
- p50 latency <50ms
- p95 latency <100ms
- p99 latency <200ms
- Memory usage <100MB for 99% of documents

### 5.3 Usability Metrics
- Setup time <5 minutes
- Clear error messages
- Comprehensive documentation
- Example code and use cases

## 6. Out of Scope
- Real-time streaming processing
- Distributed processing
- Image/PDF text extraction
- Audio/video transcription
- Database integration
- Cloud deployment
- User authentication/authorization
- Multi-language NER models (English only for v1)

## 7. Future Considerations
- Plugin architecture for custom detectors
- Additional output formats (XML, CSV)
- Confidence scoring for detections
- Differential privacy techniques
- WebAssembly compilation for browser use