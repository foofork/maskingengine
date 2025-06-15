# MaskingEngine Features Overview

MaskingEngine is a comprehensive PII detection and masking solution designed for privacy-first AI pipelines. This document provides a detailed overview of all features and capabilities.

## 🔒 Core Privacy Features

### Local-First Processing
- **Zero External Dependencies**: All processing happens locally on your infrastructure
- **No Network Calls**: No data ever leaves your environment
- **No Telemetry**: Zero usage tracking or data collection
- **Complete Data Sovereignty**: You maintain full control over your sensitive data

### Deterministic Masking
- **Consistent Placeholders**: Same PII value always gets the same placeholder within a session
- **Hash-Based Generation**: Placeholders use content hashes for consistency
- **Type-Specific Formats**: Different PII types get distinct placeholder patterns
- **Collision Resistant**: Multiple hash layers prevent placeholder conflicts

**Example:**
```
Original: "Contact john@example.com or jane@example.com"
Masked:   "Contact <<EMAIL_7A9B2C_1>> or <<EMAIL_7A9B2C_2>>"
```

### Reversible Masking (Rehydration)
- **Complete Restoration**: Original PII can be perfectly restored from masked content
- **Session-Based Storage**: Mask maps stored securely for later retrieval  
- **Format Preservation**: JSON, HTML, and text structure maintained through the process
- **Validation & Compatibility**: Comprehensive checks ensure safe rehydration

---

## 🧠 Detection Technologies

### Dual-Engine Detection System

#### Regex Detection Engine
- **Performance**: < 50ms processing time for typical content
- **Pattern Types**: 16+ built-in PII types (emails, phones, SSNs, credit cards, IPs)
- **Customizable**: YAML-based pattern packs for organization-specific PII
- **Multilingual**: Patterns for US, FR, DE, ES, and other regions
- **Validation**: Built-in validation (e.g., Luhn check for credit cards)

#### NER (Named Entity Recognition) Engine  
- **Model**: DistilBERT (`yonigo/distilbert-base-multilingual-cased-pii`)
- **Multilingual**: Supports multiple languages out of the box
- **Contextual**: Understands context to reduce false positives
- **Entity Types**: EMAIL, TEL, SOCIALNUMBER detection
- **Confidence Scoring**: Configurable confidence thresholds

### Intelligent Deduplication
- **Overlap Resolution**: Automatically handles overlapping detections from multiple engines
- **Priority System**: Regex takes precedence for structured data, NER for contextual
- **Conflict Resolution**: Smart merging of detection results
- **Performance Optimization**: Eliminates redundant processing

---

## 📝 Content Format Support

### Text Processing
- **Plain Text**: Full support for unstructured text content
- **Line Preservation**: Maintains original formatting and line breaks
- **Unicode Support**: Full international character support
- **Large Content**: Handles documents of any reasonable size

### JSON Processing
- **Structure Preservation**: Maintains exact JSON structure after masking
- **Recursive Traversal**: Processes nested objects and arrays
- **Key Safety**: Only values are masked, keys remain unchanged
- **Type Preservation**: Numbers, booleans, nulls remain unchanged

**Example:**
```json
// Original
{
  "user": "john@example.com",
  "phone": "555-123-4567",
  "age": 30
}

// Masked
{
  "user": "<<EMAIL_7A9B2C_1>>",
  "phone": "<<PHONE_4D8E1F_1>>", 
  "age": 30
}
```

### HTML Processing
- **Tag Preservation**: HTML structure and attributes maintained
- **Content-Only Masking**: Only text content is processed, markup stays intact
- **Nested Elements**: Handles complex nested HTML structures
- **Attribute Safety**: Attributes are not modified during processing

**Example:**
```html
<!-- Original -->
<div class="contact">
  <p>Email: <a href="mailto:john@example.com">john@example.com</a></p>
</div>

<!-- Masked -->
<div class="contact">
  <p>Email: <a href="mailto:john@example.com"><<EMAIL_7A9B2C_1>></a></p>
</div>
```

### Auto-Format Detection
- **Intelligent Recognition**: Automatically detects content format
- **Fallback Handling**: Graceful degradation for ambiguous content
- **Override Support**: Manual format specification when needed

---

## ⚙️ Configuration & Customization

### Pattern Pack System
- **YAML-Based**: Human-readable configuration files
- **Modular Design**: Load multiple pattern packs simultaneously
- **Tiered Priority**: Three-tier system for pattern precedence
- **Community Extensible**: Share and reuse pattern packs across teams

#### Built-in Pattern Types
| Pattern Type | Description | Example |
|--------------|-------------|---------|
| EMAIL | Email addresses | john@example.com |
| US_PHONE | US phone numbers | 555-123-4567 |
| INTERNATIONAL_PHONE | International formats | +33 1 23 45 67 89 |
| US_SSN | Social Security Numbers | 123-45-6789 |
| CREDIT_CARD_NUMBER | Credit card numbers | 4111-1111-1111-1111 |
| IPV4 | IPv4 addresses | 192.168.1.1 |
| IPV6 | IPv6 addresses | 2001:db8::1 |
| FR_PHONE_NUMBER | French phone numbers | 01 23 45 67 89 |
| SPANISH_DNI | Spanish DNI numbers | 12345678Z |
| GERMAN_TAX_ID | German tax IDs | 12345678901 |
| FRENCH_SSN | French social security | 1234567890123 |

### Whitelist Support
- **Flexible Exclusions**: Exclude specific terms from masking
- **Pattern-Based**: Support for regex patterns in whitelist
- **Context-Aware**: Whitelist applies across all detection engines
- **Runtime Configuration**: Change whitelist without restarting

**Example:**
```python
config = Config(
    whitelist=["support@company.com", "noreply@company.com"]
)
# These emails will never be masked
```

### Performance Modes
- **Regex-Only Mode**: Maximum speed (< 50ms) for structured data
- **NER+Regex Mode**: Best accuracy for unstructured text
- **Hybrid Mode**: Automatic selection based on content type
- **Custom Configuration**: Fine-tune detection engines per use case

### Validation Options
- **Strict Validation**: Enable format validation (Luhn check for cards)
- **Confidence Thresholds**: Set minimum confidence for NER detections
- **Pattern Verification**: Validate patterns before masking
- **Quality Control**: Comprehensive input validation

---

## 🔄 Rehydration System

### Session-Based Workflows
Perfect for AI pipeline integration where you need to:
1. Mask PII before sending to LLM
2. Process with external AI service
3. Restore original PII in the response

```python
# Step 1: Sanitize with session
pipeline = RehydrationPipeline(sanitizer, storage)
masked_content, storage_path = pipeline.sanitize_with_session(
    content="Contact john@example.com",
    session_id="user_123_conversation_456"
)

# Step 2: Send masked_content to LLM
llm_response = llm.process(masked_content)

# Step 3: Rehydrate LLM response
original_response = pipeline.rehydrate_with_session(
    llm_response, "user_123_conversation_456"
)
```

### Storage Management
- **Persistent Storage**: JSON-based storage for session durability
- **Automatic Cleanup**: Configurable session expiration and cleanup
- **Session Isolation**: Each session completely isolated from others
- **Storage Flexibility**: Configurable storage directory and format

### Validation & Safety
- **Compatibility Checking**: Ensures mask map matches content before rehydration
- **Placeholder Validation**: Verifies placeholder format integrity
- **Missing Key Detection**: Identifies missing mappings before processing
- **Error Recovery**: Graceful handling of corrupted or incomplete data

---

## 🌐 Multiple Interface Support

### Python SDK
```python
from maskingengine import Sanitizer, Config

# Basic usage
sanitizer = Sanitizer()
masked, mask_map = sanitizer.sanitize("Contact john@example.com")

# Advanced configuration
config = Config(
    pattern_packs=["default", "enterprise"],
    whitelist=["support@company.com"],
    regex_only=True
)
sanitizer = Sanitizer(config)
```

### Command Line Interface
```bash
# Basic masking
maskingengine mask input.txt -o output.txt

# Advanced options
maskingengine mask input.txt \
  --regex-only \
  --pattern-packs default enterprise \
  --whitelist "support@company.com" \
  -o output.txt

# Session-based workflow
maskingengine session-sanitize input.txt session123 -o masked.txt
echo "Response with <<EMAIL_7A9B2C_1>>" | \
  maskingengine session-rehydrate --stdin session123
```

### REST API
```bash
# Basic sanitization
curl -X POST "http://localhost:8000/sanitize" \
  -H "Content-Type: application/json" \
  -d '{"content": "Contact john@example.com"}'

# Session workflow
curl -X POST "http://localhost:8000/session/sanitize" \
  -H "Content-Type: application/json" \
  -d '{"content": "Contact john@example.com", "session_id": "user123"}'

curl -X POST "http://localhost:8000/session/rehydrate" \
  -H "Content-Type: application/json" \
  -d '{"masked_content": "<<EMAIL_7A9B2C_1>>", "session_id": "user123"}'
```

---

## 🚀 Performance Features

### Speed Optimization
- **Regex-Only Mode**: Sub-50ms processing for structured content
- **Pattern Caching**: Pre-compiled patterns cached in memory
- **Parallel Processing**: Regex and NER engines run concurrently
- **Minimal Allocation**: Memory-efficient processing pipeline

### Memory Management
- **Lazy Loading**: NER model loaded only when needed
- **Shared Resources**: Model shared across multiple requests
- **Efficient Storage**: Optimized data structures for large content
- **Garbage Collection**: Automatic cleanup of temporary objects

### Scalability
- **Stateless Design**: Horizontal scaling without session affinity
- **Concurrent Processing**: Thread-safe for multi-request environments
- **Resource Limits**: Configurable memory and processing limits
- **Load Balancer Ready**: Works seamlessly behind load balancers

---

## 🛡️ Production Features

### Error Handling
- **Graceful Degradation**: Continues processing despite individual pattern failures
- **Comprehensive Logging**: Detailed error information without exposing PII
- **Input Validation**: Thorough validation of all inputs
- **Recovery Mechanisms**: Automatic recovery from transient failures

### Monitoring & Health Checks
- **Health Endpoints**: Built-in health check for load balancers
- **Status Monitoring**: Real-time status of all components
- **Performance Metrics**: Processing time and throughput tracking
- **Configuration Validation**: Startup validation of all settings

### Security
- **Input Sanitization**: Protection against injection attacks
- **Memory Safety**: Secure handling of sensitive data in memory
- **Access Control Ready**: Framework for authentication integration
- **Audit Trail**: Comprehensive logging for security compliance

### Deployment Ready
- **Container Support**: Docker-ready with minimal dependencies
- **Environment Configuration**: Full environment variable support
- **Process Management**: Production-ready process handling
- **Resource Management**: Configurable resource limits and quotas

---

## 🔌 Integration Features

### Framework Integrations
```python
# LangChain integration
from langchain.text_splitter import RecursiveCharacterTextSplitter
from maskingengine import Sanitizer

class PrivacyTextSplitter(RecursiveCharacterTextSplitter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sanitizer = Sanitizer()
    
    def split_text(self, text):
        masked, _ = self.sanitizer.sanitize(text)
        return super().split_text(masked)

# Pandas integration
import pandas as pd
sanitizer = Sanitizer()
df["message"] = df["message"].apply(lambda x: sanitizer.sanitize(str(x))[0])
```

### API Gateway Integration
- **OpenAPI Specification**: Full OpenAPI 3.0 documentation
- **Standard HTTP Status Codes**: Proper error handling
- **CORS Support**: Cross-origin request handling
- **Rate Limiting Ready**: Framework for rate limiting integration

### Database Integration
- **Batch Processing**: Efficient processing of large datasets
- **Stream Processing**: Support for real-time data streams
- **Transaction Safety**: Works within database transactions
- **Backup Integration**: Compatible with backup and archival systems

---

## 📊 Analytics & Insights

### Detection Metrics
- **Detection Counts**: Number of PII entities found per content type
- **Pattern Effectiveness**: Which patterns are most/least effective
- **False Positive Tracking**: Monitor and tune detection accuracy
- **Performance Profiling**: Detailed timing of each processing stage

### Usage Analytics
- **Content Type Distribution**: Track most common content formats
- **Pattern Pack Usage**: Monitor which patterns are used most
- **Session Analytics**: Rehydration success rates and timing
- **Error Pattern Analysis**: Common failure modes and causes

---

## 🌍 Internationalization

### Language Support
- **Multilingual NER**: DistilBERT model supports multiple languages
- **Localized Patterns**: Country and language-specific pattern packs
- **Unicode Handling**: Full international character support
- **Regional Formats**: Support for regional phone, ID, and date formats

### Cultural Sensitivity
- **Regional Compliance**: Patterns designed for local privacy regulations
- **Cultural Patterns**: Recognition of culture-specific PII formats
- **Flexible Configuration**: Easy adaptation for different regions
- **Community Contributions**: Framework for community-contributed patterns

---

## 🔮 Extensibility Features

### Plugin Architecture
- **Custom Detectors**: Easy integration of custom detection engines
- **Custom Parsers**: Support for specialized content formats
- **Custom Validators**: Add domain-specific validation logic
- **Event Hooks**: Pre/post processing hooks for custom logic

### Pattern Ecosystem
- **Community Patterns**: GitHub-based sharing of pattern packs
- **Version Management**: Semantic versioning for pattern packs
- **Dependency Management**: Pattern pack dependencies and conflicts
- **Testing Framework**: Automated testing for custom patterns

### Future-Ready Design
- **Modular Architecture**: Easy addition of new capabilities
- **Configuration Driven**: Behavior modification without code changes
- **Standards Compliant**: Following industry best practices
- **Backward Compatibility**: Commitment to API stability

This comprehensive feature set makes MaskingEngine suitable for a wide range of use cases, from simple PII redaction to complex AI pipeline integration, while maintaining the highest standards for privacy, performance, and reliability.