# Changelog

All notable changes to MaskingEngine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-15

### Added
- 🚀 **Core Features**
  - Privacy-first PII detection and masking
  - Multilingual NER using DistilBERT (yonigo/distilbert-base-multilingual-cased-pii)
  - Regex-only mode for <50ms performance
  - YAML-based pattern pack system for extensibility
  - Format-aware parsing (JSON, HTML, plain text)
  - Deterministic masking with <<TYPE_HASH_INDEX>> placeholders

- 🔁 **Rehydration System**
  - Complete rehydration pipeline for restoring original PII
  - Session-based storage and retrieval
  - Validation and compatibility checking
  - Automatic cleanup and management

- 🔧 **Multiple Interfaces**
  - Python SDK with `Sanitizer`, `Rehydrator`, `RehydrationPipeline`
  - CLI with mask, rehydrate, and session commands
  - REST API with sanitize, rehydrate, and session endpoints
  - Full configuration support across all interfaces

- 🧩 **Pattern Packs**
  - Default pack with 16+ PII types (email, phone, SSN, IP, credit cards)
  - International patterns (Spanish DNI, German Tax ID, French SSN, etc.)
  - Custom pattern pack support
  - YAML-based configuration without context keyword requirements

- ⚙️ **Configuration Options**
  - Whitelist support for excluding specific terms
  - Regex-only mode for maximum performance
  - Strict validation (Luhn check for credit cards)
  - Custom placeholder prefixes
  - NER confidence thresholds
  - Pattern pack selection

- 🛡️ **Production-Ready Error Handling**
  - Graceful degradation for invalid inputs
  - YAML parsing error recovery
  - File I/O and permission error handling
  - Network and dependency fault tolerance
  - Automatic fallbacks and warnings

### Security
- Local-first processing (no network calls)
- No telemetry or data collection
- Secure mask map storage with session isolation
- Production-ready input validation and sanitization

### Performance
- Regex-only mode: <50ms processing
- NER+Regex mode: <200ms processing  
- Memory-efficient with configurable limits
- Concurrent access support
- Optimized pattern compilation and caching