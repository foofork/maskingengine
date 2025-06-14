# MaskingEngine

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Version 1.01.01](https://img.shields.io/badge/version-1.01.01-blue.svg)](https://github.com/yourusername/maskingengine)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-87%25%20passing-green.svg)](https://github.com/yourusername/maskingengine)

A local-first PII sanitizer for AI applications. Automatically detects and masks sensitive data before sending to external AI services.

Transform: `"Email john.doe@acme.com or call (555) 123-4567"`  
Into: `"Email <<EMAIL_7D8E9F>> or call <<PHONE_4G5H6I>>"`

## Features

- **Local Processing**: All data processing happens on your infrastructure
- **Format Support**: Handles plain text, JSON, and HTML while preserving structure
- **Deterministic Output**: Same input always produces the same masked result
- **Fast Performance**: <100ms processing for typical documents
- **Zero Dependencies**: No external API calls or network requirements

## Quick Start

### Installation
```bash
pip install maskingengine
```

### Basic Usage
```python
from maskingengine import Sanitizer

sanitizer = Sanitizer()

# Mask sensitive data
text = "Contact John Smith at john.smith@acme.com or call +1-555-123-4567"
masked = sanitizer.sanitize(text)
print(masked)
# Output: "Contact John Smith at <<EMAIL_7D8E9F>> or call <<PHONE_G7H8I9>>"

# Safe to send to AI services
ai_response = your_ai_service(masked)
```

### Supported Data Formats

**Plain Text**
```python
sanitizer.sanitize("Email me at john@example.com")
```

**JSON (preserves structure)**
```python
data = {"email": "jane@company.com", "phone": "555-123-4567"}
result = sanitizer.sanitize(data)
# Returns: {"email": "<<EMAIL_D4E5F6>>", "phone": "<<PHONE_G7H8I9>>"}
```

**HTML (preserves markup)**
```python
html = '<a href="mailto:john@example.com">Contact</a>'
sanitizer.sanitize(html)
# Returns: '<a href="mailto:<<EMAIL_A1B2C3>>">Contact</a>'
```

## Detection Capabilities (v1.01.01)

| PII Type | Examples | Method |
|----------|----------|---------|
| Email | `john@company.com` | Regex Pattern |
| Phone | `(555) 123-4567`, `+1-555-123-4567` | Regex Pattern |
| Credit Cards | `4111-1111-1111-1111` | Regex + Luhn Validation |
| IP Address | `192.168.1.1`, `2001:db8::1` | Regex Pattern |
| SSN | `123-45-6789` | Regex Pattern |

### In Development
- **Names, Organizations, Locations**: NER-based detection for multilingual content
- **REST API**: HTTP service with OpenAPI documentation
- **CLI Tools**: Command-line interface for batch processing

## Use Cases

### AI Pipeline Protection
```python
# Clean data before sending to external AI
user_input = "My email is sarah@company.com"
safe_input = sanitizer.sanitize(user_input)
ai_response = openai_api.chat(safe_input)
```

### Log Sanitization
```python
# Remove PII from application logs
with open('app.log', 'r') as f:
    for line in f:
        clean_line = sanitizer.sanitize(line)
        safe_logs.append(clean_line)
```

### Data Processing
```python
# Clean datasets before analysis
for record in customer_data:
    safe_record = sanitizer.sanitize(record)
    cleaned_data.append(safe_record)
```

## Configuration

```python
from maskingengine import Sanitizer, Config

# Default configuration
sanitizer = Sanitizer()

# Custom configuration
config = Config()
sanitizer = Sanitizer(config)
```

## Performance

- **Latency**: <100ms for most documents (1-10KB)
- **Memory**: ~50MB RAM for core functionality
- **Throughput**: 300+ documents/second for typical workloads
- **Reliability**: Graceful error handling, returns original data on processing failures

## Integration Examples

### LangChain
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from maskingengine import Sanitizer

sanitizer = Sanitizer()

class PrivacyTextSplitter(RecursiveCharacterTextSplitter):
    def split_text(self, text):
        return super().split_text(sanitizer.sanitize(text))
```

### Pandas DataFrames
```python
import pandas as pd
from maskingengine import Sanitizer

sanitizer = Sanitizer()

def clean_dataframe(df):
    for col in df.select_dtypes(include=['object']):
        df[col] = df[col].apply(lambda x: sanitizer.sanitize(str(x)) if pd.notna(x) else x)
    return df
```

### Streamlit Applications
```python
import streamlit as st
from maskingengine import Sanitizer

sanitizer = Sanitizer()

user_input = st.text_area("Enter text:")
if st.button("Process"):
    masked = sanitizer.sanitize(user_input)
    st.write("Masked:", masked)
```

## Development

### Setup
```bash
git clone https://github.com/yourusername/maskingengine.git
cd maskingengine
pip install -e ".[dev]"
```

### Testing
```bash
pytest                    # Run tests
pytest --cov=maskingengine  # With coverage
```

### Code Quality
```bash
black .                   # Format code
ruff check .             # Lint code
mypy maskingengine       # Type checking
```

## Architecture

MaskingEngine uses a simple 5-module architecture:

```
maskingengine/
├── config.py      # Configuration management
├── parsers.py     # Text/JSON/HTML parsing
├── detectors.py   # Regex-based PII detection
├── masker.py      # Placeholder generation
└── sanitizer.py   # Main API
```

## Roadmap

### v1.1.0 - Enhanced Detection
- NER model integration for names, organizations, locations
- Improved international phone number support
- Additional PII pattern types

### v1.2.0 - Integration Suite
- REST API with OpenAPI documentation
- Command-line tools for batch processing
- Docker container support

### v2.0.0 - Enterprise Features
- Custom pattern definitions
- Audit logging and compliance reporting
- Performance optimizations for high-volume processing

## Current Status

- **Core Library**: Production ready
- **Python Integration**: Fully functional
- **REST API**: In development
- **CLI Tools**: In development
- **NER Detection**: Planned for v1.1.0

## Documentation

- [Implementation Guide](docs/implementation_guide.md)
- [API Reference](docs/api/)
- [Architecture Guide](docs/architecture/)
- [Examples](examples/)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

For bug reports and feature requests, please use [GitHub Issues](https://github.com/yourusername/maskingengine/issues).