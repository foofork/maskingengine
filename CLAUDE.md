# Claude Code Integration Guide - MaskingEngine

This document provides comprehensive guidance to Claude when working with the MaskingEngine codebase.

## Project Overview
MaskingEngine is a local-first, privacy-by-design PII (Personally Identifiable Information) sanitizer system. It acts as a privacy firewall for AI workflows, enabling applications to safely use third-party LLMs by sanitizing sensitive user data before it leaves the application's trust boundary.

### Key Features
- Deterministic, reversible masking with content-based placeholders
- Dual detection: High-confidence regex patterns + multilingual NER model
- Highly configurable via single API object
- Multiple interfaces: Python library, REST API, and CLI
- Format support: Plain text, JSON, and HTML
- Local processing with zero telemetry

## Development Methodology

### SPARC (Specification, Pseudocode, Architecture, Refinement, Completion)
1. **Specification**: Define clear requirements and acceptance criteria
2. **Pseudocode**: Plan implementation logic before coding
3. **Architecture**: Design modular, testable components
4. **Refinement**: Iterate based on tests and feedback
5. **Completion**: Ensure all tests pass and documentation is complete

### TDD (Test-Driven Development)
1. Write failing tests first
2. Implement minimal code to pass tests
3. Refactor while keeping tests green
4. Document as you go

## Architecture

### Core Components
- **Detectors**: Regex and NER-based PII detection
- **Pipeline**: Orchestrates detection, validation, and whitelist filtering
- **Masking Engine**: Deterministic placeholder generation and rehydration
- **Parsers**: Handle different content formats (text, JSON, HTML)
- **Config**: Pydantic-based configuration management

## Code Conventions
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Style**: PEP 8 with 100-char lines, Black formatting, Ruff linting
- **Patterns**: Factory pattern for parsers, Strategy pattern for detectors
- **Testing**: TDD with pytest, minimum 90% coverage, property-based tests

## Directory Structure
```
maskingengine/
├── maskingengine/          # Main package
│   ├── core/              # Core functionality
│   │   ├── config.py      # Configuration management
│   │   ├── pipeline.py    # Sanitization pipeline
│   │   ├── masking.py     # Masking/rehydration engine
│   │   ├── parsers.py     # Content parsers
│   │   └── sanitizer.py   # Main API interface
│   ├── detectors/         # PII detection modules
│   │   ├── regex_detector.py  # Regex-based detection
│   │   └── ner_detector.py    # NER model detection
│   ├── api/               # REST API (FastAPI)
│   └── cli/               # CLI interface
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── fixtures/         # Test data
├── docs/                 # Documentation
├── examples/             # Usage examples
└── coordination/         # Claude-flow coordination
```

## Development Workflow
1. **SPARC Planning**: Define specs, write pseudocode, design architecture
2. **Write Tests First**: Create failing tests for new functionality
3. **Implement**: Write minimal code to pass tests
4. **Refactor**: Improve code while keeping tests green
5. **Document**: Update docs and examples
6. **Validate**: Run full test suite, linters, type checkers

### Testing Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=maskingengine

# Run specific test file
pytest tests/unit/test_regex_detector.py

# Run linters
black .
ruff .
mypy maskingengine
```

## Important Considerations
- **Security**: Fail fast on errors, no PII logging, secure defaults
- **Performance**: <100ms latency target, 1.5GB RAM for NER model
- **Compatibility**: Python 3.8+, cross-platform, Docker-ready

## Common Tasks
- **Add a new feature**: Follow TDD - test first, implement, refactor
- **Fix a bug**: Write failing test, fix, ensure no regressions
- **Update documentation**: Keep README, API docs, examples in sync

## Dependencies
- **phonenumbers**: International phone number validation
- **transformers**: Hugging Face models for NER
- **torch**: PyTorch for model inference
- **fastapi**: REST API framework
- **pydantic**: Data validation and settings
- **click**: CLI framework

## Troubleshooting
- Model loading issues: Check CUDA/MPS availability, fallback to CPU
- Memory errors: Ensure 1.5GB+ RAM available for NER model
- Performance: Use regex-only mode for faster processing
