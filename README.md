# MaskingEngine

Privacy-first, blazing-fast PII redaction for AI pipelines.

MaskingEngine is a local-first, multilingual PII sanitizer built for AI applications, logs, and data workflows. It detects and masks emails, phone numbers, names, IDs, and more before text is sent to large language models or stored in logs.

**Input:**   `Contact John Smith at john@example.com or call 555-123-4567`  
**Output:**  `Contact John Smith at <<EMAIL_7A9B2C_1>> or call <<PHONE_4D8E1F_1>>`

## 🚀 Features

* 🧠 **Multilingual NER** — DistilBERT model for contextual PII detection in 100+ languages
* ⚡ **Regex-only mode** — No model loading, <50ms masking for structured PII
* 🧩 **YAML pattern packs** — Easily extend detection for your org or domain
* 💬 **Format-aware** — Preserves structure in JSON, HTML, plain text
* 🔐 **Fully local** — No network calls, no telemetry, production-ready
* 🔁 **Optional Rehydration** — Restore original PII when needed (most use cases don't need this)
* 🔧 **CLI, REST API, SDK** — Drop into LangChain, Python pipelines, or microservices

## 🛠 Installation

### From Source (Current)
```bash
# Clone the repository
git clone https://github.com/foofork/maskingengine.git
cd maskingengine

# Install with pip
pip install .

# Or install in development mode
pip install -e .
```

### Requirements
- Python 3.8+
- Dependencies: PyTorch, Transformers, FastAPI (for API), Click (for CLI)

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Verify installation
maskingengine test
```

> **Note**: PyPI package coming soon! For now, install from source.

### Quick Installation Test
```bash
# Test CLI
echo "Email: test@example.com" | maskingengine mask --stdin --regex-only

# Test Python SDK
python -c "from maskingengine import Sanitizer; print('✅ Installation successful!')"
```

## 🚀 Quick Start

```bash
# CLI (Regex-only mode)
echo "Email john@example.com or call 555-123-4567" | maskingengine mask --stdin --regex-only
```

```python
# Python usage
from maskingengine import Sanitizer

sanitizer = Sanitizer()
masked, mask_map = sanitizer.sanitize("Email john@example.com")
print(masked)
# => "Email <<EMAIL_7A9B2C_1>>"

# mask_map contains original values for optional restoration
# Most use cases just use 'masked' and discard 'mask_map'
```

## 🔎 What It Detects

### Built-in (Regex-based)

| Type | Example | Global Support |
|------|---------|----------------|
| Email | `john@example.com` | ✅ Universal |
| Phone | `+1 555-123-4567` | ✅ US/EU/Intl |
| IP Address | `192.168.1.1` | ✅ IPv4/IPv6 |
| Credit Card | `4111-1111-1111-1111` | ✅ Luhn-validated |
| SSN | `123-45-6789` | 🇺🇸 US only |
| ID Numbers | `X1234567B, BSN, INSEE` | 🇪🇸 🇳🇱 🇫🇷 etc. |

### NER-based (DistilBERT model)

| Type | Example | Languages |
|------|---------|-----------|
| Email | `john@example.com` | Multilingual |
| Phone | `555-123-4567` | Multilingual |
| Social Numbers | `123-45-6789` | Multilingual |

*Note: NER model complements regex patterns and excels at contextual detection*

## 🧩 Pattern Packs

Define your own redaction rules using YAML:

```yaml
# patterns/custom.yaml
name: "custom"
description: "Enterprise-specific patterns"
version: "1.0.0"

patterns:
  - name: EMPLOYEE_ID
    description: "Employee ID numbers"
    tier: 1
    language: "universal"
    patterns:
      - '\bEMP\d{6}\b'
```

Then load:
```python
from maskingengine import Config, Sanitizer
config = Config(pattern_packs=["default", "custom"])
sanitizer = Sanitizer(config)
```

## 📄 Input Formats

```python
# JSON - structure preserved
result, mask_map = sanitizer.sanitize({"email": "jane@company.com"}, format="json")

# HTML - tags preserved
html = '<a href="mailto:john@example.com">Email</a>'
result, mask_map = sanitizer.sanitize(html, format="html")

# Plain text - auto-detected
text = "Contacta a María García en maria@empresa.es"  
result, mask_map = sanitizer.sanitize(text)
```

## ⚙️ Configuration Options

```python
config = Config(
    regex_only=True,                    # Speed mode (no NER)
    pattern_packs=["default", "custom"], # Load specific pattern packs
    whitelist=["support@company.com"],   # Terms to exclude from masking
    min_confidence=0.9,                 # NER confidence threshold
    strict_validation=True              # Enable validation (Luhn check, etc.)
)
sanitizer = Sanitizer(config)
```

## 🖥 REST API

Start the API server:
```bash
python run_api.py
# API available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

Example usage:
```bash
curl -X POST http://localhost:8000/sanitize \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Email john@example.com",
    "format": "text",
    "regex_only": true
  }'
```

## 💡 Framework Integration Examples

```python
# LangChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from maskingengine import Sanitizer
sanitizer = Sanitizer()

class PrivacyTextSplitter(RecursiveCharacterTextSplitter):
  def split_text(self, text):
    masked, _ = sanitizer.sanitize(text)
    return super().split_text(masked)

# Pandas
import pandas as pd
from maskingengine import Sanitizer
sanitizer = Sanitizer()
df["message"] = df["message"].apply(lambda x: sanitizer.sanitize(str(x))[0])
```

## 🧪 Performance Modes

| Mode | Speed | Accuracy | Use Case |
|------|-------|----------|----------|
| Regex-only | <50ms | High for structured PII | Logs, structured data |
| NER + Regex | <200ms* | Highest | Unstructured text, contextual |
| Custom patterns | <100ms | Domain-specific | Enterprise rules |

*Note: First NER run includes ~8s model loading time. Subsequent runs are <200ms.*

## 📦 CLI Usage

```bash
# Regex-only (fastest)
maskingengine mask input.txt --regex-only -o output.txt

# Custom patterns
maskingengine mask input.txt --pattern-packs default custom -o output.txt

# From stdin
echo "Call 555-123-4567" | maskingengine mask --stdin --regex-only
```

## 📚 Documentation

### Core Guides
* **[Workflow Guide](docs/workflows.md)** - Visual workflow diagrams and decision guide
* **[API Reference](docs/api.md)** - Complete REST API documentation
* **[Features Overview](docs/features.md)** - Comprehensive feature documentation  
* **[Usage Examples](docs/examples.md)** - Python, CLI, API, and framework examples
* **[Architecture Overview](docs/architecture.md)** - System design and components

### Customization & Advanced Usage
* **[Custom Pattern Packs](docs/patterns.md)** - Create organization-specific PII patterns
* **[Performance & Production](docs/architecture.md#performance-architecture)** - Scaling and deployment guidance

### Getting Started
* **[Quick Start](#-quick-start)** - Basic usage examples
* **[Installation](#installation)** - Setup instructions
* **[CLI Usage](#-cli-usage)** - Command-line interface guide

## 🔁 Rehydration System

**Rehydration is completely optional** — most use cases only need sanitization for permanent PII removal (logs, analytics, training data).

For AI pipeline integration, MaskingEngine can restore original PII after LLM processing:

```python
from maskingengine import RehydrationPipeline, Sanitizer, RehydrationStorage

# Setup pipeline
sanitizer = Sanitizer()
storage = RehydrationStorage()
pipeline = RehydrationPipeline(sanitizer, storage)

# Step 1: Mask before sending to LLM
masked_content, storage_path = pipeline.sanitize_with_session(
    "Contact john@example.com about the project", 
    session_id="user_123"
)

# Step 2: Send masked_content to LLM
llm_response = llm.process(masked_content)

# Step 3: Restore original PII in response
final_response = pipeline.rehydrate_with_session(llm_response, "user_123")
```

### Common Workflows:
* ✅ **Sanitize-only**: Logs, analytics, training data (no rehydration needed)
* 🔄 **Round-trip**: AI pipelines where you restore PII in responses

📖 **[Complete examples and patterns →](docs/examples.md#session-based-workflow)**

## 🤝 Contributing

1. Fork and clone
2. Add tests for new features
3. Submit a PR with a clear description

We welcome contributors from privacy, AI, and data tooling backgrounds.

## 🔐 License

MIT License. Fully open-source and local-first — no cloud APIs required.