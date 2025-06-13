# MaskingEngine

A local-first, privacy-by-design PII (Personally Identifiable Information) sanitizer system. MaskingEngine acts as a privacy firewall for AI workflows, enabling applications to safely use third-party LLMs by sanitizing sensitive user data before it leaves the application's trust boundary.

## Features

- **Deterministic, Reversible Masking**: Consistent placeholders that can be reversed
- **Dual Detection Methods**: High-confidence regex patterns + multilingual NER model
- **Highly Configurable**: Single configuration object controls all behaviors
- **Multiple Interfaces**: Python library, REST API, and CLI
- **Privacy-First**: Local processing, no telemetry, fails fast on errors
- **Format Support**: Plain text, JSON, and HTML

## Quick Start

### Installation

```bash
pip install maskingengine
```

### Basic Usage

```python
from maskingengine import sanitize, rehydrate

# Sanitize sensitive data
original = "Contact John Doe at john.doe@example.com"
masked_text, rehydration_map = sanitize(original)
print(masked_text)  # "Contact <<PERSON_a1b2c3d4>> at <<EMAIL_e5f6g7h8>>"

# Use with LLM
llm_response = call_your_llm(masked_text)

# Restore original data
final_text = rehydrate(llm_response, rehydration_map)
```

### Configuration

```python
config = {
    "enable_regex": True,
    "enable_ner": True,
    "confidence_threshold": 0.85,
    "whitelist": ["Acme Corp", "Project Phoenix"],
    "placeholder_prefix": "<<",
    "placeholder_suffix": ">>",
    "logging_enabled": False,
    "max_input_characters": 50000
}

masked_text, map = sanitize(original, config)
```

## V1.0 Detected PII Types

### Regex Detection (High-Confidence)
- Email addresses
- Phone numbers (international formats)
- Credit card numbers (Visa, MasterCard, Amex, etc.)
- IP addresses (IPv4 and IPv6)

### NER Detection (Multilingual)
- Person names
- Locations (cities, countries)
- Organizations

## Model Information

MaskingEngine uses `distilbert-base-multilingual-cased` for NER detection:
- **Size**: ~550MB download
- **Memory**: Requires ~1.5GB RAM
- **Languages**: 100+ languages supported
- **Offline**: Model runs locally, no internet required

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/maskingengine.git
cd maskingengine

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linters
black .
ruff .
mypy .
```

## License

MIT License - see LICENSE file for details.