# MaskingEngine

[![PyPI version](https://badge.fury.io/py/maskingengine.svg)](https://pypi.org/project/maskingengine/)
[![Python Support](https://img.shields.io/pypi/pyversions/maskingengine.svg)](https://pypi.org/project/maskingengine/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> ⚠️ Large Language Models don't need to know everything.

**MaskingEngine** is a privacy-first tool that removes sensitive personal information (PII) before it reaches AI systems. Whether you're building AI-powered applications, managing logs, or training models—**mask your data first**.

Built to work locally, at scale, and across languages.

**Example:**

```text
Input:  Patient MRN-1234567 contacted María at maria@hospital.es from IP 192.168.1.100.
        SSN: 123-45-6789, Credit Card: 4111-1111-1111-1111
Output: Patient <<MEDICAL_RECORD_NUMBER_A1B2C3_1>> contacted María at <<EMAIL_7D9E2F_1>>
        from IP <<IPV4_4G8H1J_1>>. SSN: <<US_SSN_9K3L5M_1>>, Credit Card: <<CREDIT_CARD_NUMBER_2N6P4Q_1>>
```

---

## 🚀 Why Use MaskingEngine?

* 🛡 **LLMs Don't Need to Know Everything** – Redact sensitive data before inference
* 🌍 **Multilingual** – Contextual PII detection in 100+ languages (DistilBERT)
* 🧱 **Modular + Swappable** – Bring your own NER model or pattern rules
* ⚡ **Blazing Fast Regex Mode** – <50ms for structured data, logs, pipelines
* 🧩 **Unlimited Pattern Packs** – Load any number of custom YAML pattern files
* 🎯 **Smart Whitelisting** – Exclude specific terms from masking
* 📺 **Streaming Support** – Process large files efficiently chunk by chunk
* 🧠 **Context-Aware** – Uses machine learning to detect hidden PII in text
* 🔐 **100% Local-First** – No cloud API, no telemetry, just privacy
* 🔁 **Optional Rehydration** – Restore original PII in LLM responses if needed
* 🧰 **Flexible Interfaces** – Use via CLI, REST API, or Python SDK

---

## 🧭 Who Is This For?

* **AI Developers** – Pre-process text before it hits your LLM
* **Security Engineers** – Sanitize logs and structured inputs
* **Data Teams** – Redact training and analytics data on the fly
* **Enterprises** – Enforce policy with custom detection rules and profiles

---

## 🛠 Installation

### 📦 Install via pip

```bash
pip install maskingengine
```

#### Variants:

```bash
pip install maskingengine[minimal]  # Regex-only mode
pip install maskingengine[api]      # Add REST API support
pip install maskingengine[dev]      # Dev tools
```

### 🛠 Install from Source

```bash
git clone https://github.com/foofork/maskingengine.git
cd maskingengine
pip install -e .
```

### 🐳 Run via Docker

```bash
docker pull maskingengine:latest
# Or build manually
docker build -t maskingengine:latest .
```

---

## ✅ Quick Start

### 1. First Time? Start Here

```bash
# Interactive setup guide
maskingengine getting-started

# See available profiles
maskingengine list-profiles
```

### 2. CLI Usage

```bash
# Fast regex-only mode (recommended for logs, structured data)
echo "Email john@example.com or call 555-123-4567" | maskingengine mask --stdin --regex-only

# Use pre-built profiles
maskingengine mask input.txt --profile healthcare-en -o masked.txt

# Test with sample text
maskingengine test-sample "Contact john@example.com, SSN: 123-45-6789" --profile minimal
```

### 3. Python SDK

```python
from maskingengine import Sanitizer

# Basic usage
sanitizer = Sanitizer()
masked, mask_map = sanitizer.sanitize("Email john@example.com")
print(masked)  # => Email <<EMAIL_7A9B2C_1>>

# Using profiles
sanitizer = Sanitizer(profile="healthcare-en")
result = sanitizer.sanitize("Patient MRN-1234567 contacted at john@hospital.com")

# With rehydration
from maskingengine import RehydrationPipeline, RehydrationStorage
pipeline = RehydrationPipeline(Sanitizer(), RehydrationStorage())
masked, session_id = pipeline.sanitize_with_session("Contact john@example.com", "user_123")
# ... process with LLM ...
restored = pipeline.rehydrate_with_session(llm_response, "user_123")
```

---

## 🔍 What It Detects

### Built-in Regex Support

| Type         | Example                                     | Global |
| ------------ | ------------------------------------------- | ------ |
| Email        | john@example.com                            | ✅      |
| Phone        | +1 555-123-4567                             | ✅      |
| IP Address   | 192.168.1.1                                 | ✅      |
| Credit Card  | 4111-1111-1111-1111                         | ✅      |
| SSN          | 123-45-6789                                 | 🇺🇸   |
| National IDs | X1234567B, BSN, INSEE                       | 🌍     |

### NER (ML-based)

Uses DistilBERT for contextual detection of:

* Names
* Emails
* Phones
* Social IDs (e.g. SSN)

*Note: NER model is swappable for custom deployments.*

---

## 🧩 Custom Pattern Packs

Write and load your own rules:

```yaml
# custom.yaml
patterns:
  - name: EMPLOYEE_ID
    patterns: ['\bEMP\d{6}\b']
```

```python
from maskingengine import Config, Sanitizer
config = Config(pattern_packs=["default", "custom"])
sanitizer = Sanitizer(config)
```

Pattern packs are **additive** and can be combined freely.

---

## 🔧 Configuration

### Configuration Profiles

MaskingEngine comes with pre-built profiles for common use cases:

| Profile | Description | Speed | Best For |
|---------|-------------|-------|----------|
| `minimal` | Regex-only, basic PII types | ~10ms | High-speed processing, structured data |
| `standard` | Balanced regex + NER detection | ~200ms | General use, balanced speed/accuracy |
| `healthcare-en` | HIPAA-focused patterns | ~50ms | Medical records, healthcare compliance |
| `high-security` | Maximum detection with strict validation | ~300ms | Security-critical applications |

```bash
# Use a profile
maskingengine mask input.txt --profile healthcare-en -o output.txt

# Or in Python
from maskingengine import Sanitizer
sanitizer = Sanitizer(profile="healthcare-en")
```

### Custom Configuration

```python
from maskingengine import Config, Sanitizer

config = Config(
    regex_only=True,
    pattern_packs=["default", "custom"],
    whitelist=["support@company.com"],
    min_confidence=0.9,
    strict_validation=True
)
sanitizer = Sanitizer(config)
```

---

## 🌐 Input Formats

```python
# JSON
sanitizer.sanitize({"email": "jane@company.com"}, format="json")

# HTML
sanitizer.sanitize('<a href="mailto:john@example.com">Email</a>', format="html")

# Text
txt = "Contacta a María García en maria@empresa.es"
sanitizer.sanitize(txt)
```

---

## 🖥 REST API

```bash
python scripts/run_api.py
# or
docker run -p 8000:8000 maskingengine:latest
```

```bash
curl -X POST http://localhost:8000/sanitize \
  -H "Content-Type: application/json" \
  -d '{"content": "Email john@example.com", "regex_only": true}'
```

---

## ⚙️ Performance Modes

| Profile | Mode | Speed | Memory | When to Use |
|---------|------|-------|---------|-------------|
| `minimal` | Regex-only | ~10ms | Low | High-speed processing, structured data, logs |
| `healthcare-en` | Regex-only | ~50ms | Low | Medical records, HIPAA compliance |
| `standard` | Regex + NER | ~200ms | Medium | General use, balanced speed/accuracy |
| `high-security` | Regex + NER | ~300ms | Medium | Security-critical, maximum detection |
| Streaming | Any | Efficient | Low | Large files, memory-sensitive processing |

✅ Custom pattern packs supported in all modes.

**Scaling**: MaskingEngine is stateless and fast, designed to scale horizontally in microservices or distributed queues. All processing happens locally with no external dependencies.

---

## 🌀 Rehydration (Advanced Use Case)

Use rehydration when working with LLMs where sanitized input is required, but you need to restore PII in the final response — such as personalized replies, emails, or user support agents.

```python
from maskingengine import RehydrationPipeline, RehydrationStorage

pipeline = RehydrationPipeline(Sanitizer(), RehydrationStorage())
masked, session_id = pipeline.sanitize_with_session("Contact john@example.com", "user_123")
# ... call LLM ...
restored = pipeline.rehydrate_with_session(response_from_llm, "user_123")
```

---

## 🧪 Examples

### LangChain Integration

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
class PrivacyTextSplitter(RecursiveCharacterTextSplitter):
    def split_text(self, text):
        masked, _ = sanitizer.sanitize(text)
        return super().split_text(masked)
```

### Pandas Integration

```python
df["message"] = df["message"].apply(lambda x: sanitizer.sanitize(str(x))[0])
```

---

## 📦 CLI Commands

### Getting Started
```bash
maskingengine getting-started          # Interactive guide for new users
maskingengine list-profiles            # Show available configuration profiles
maskingengine list-packs              # Show available pattern packs
maskingengine list-models             # Show available NER models
```

### Core Masking
```bash
# Basic masking
maskingengine mask input.txt --regex-only -o output.txt

# Using profiles
maskingengine mask input.txt --profile healthcare-en -o output.txt
maskingengine mask input.txt --profile minimal

# From stdin
echo "Email: john@example.com" | maskingengine mask --stdin --regex-only

# Test with sample text
maskingengine test-sample "Email: john@example.com" --profile minimal
```

### Session-Based Rehydration
```bash
# Sanitize with session storage
maskingengine session-sanitize input.txt --session-id user123 -o masked.txt

# Rehydrate using stored session
maskingengine session-rehydrate response.txt --session-id user123 -o final.txt

# Manage sessions
maskingengine sessions                 # List active sessions
maskingengine cleanup-sessions         # Clean up old sessions
```

### Configuration & Testing
```bash
maskingengine validate-config config.json    # Validate configuration
maskingengine test                           # Run comprehensive tests
```

---

## 🆕 What's New in v1.2.0

### Configuration System
- **Pre-built Profiles**: Ready-to-use configurations for healthcare, minimal processing, and high-security scenarios
- **JSON Schema Validation**: Full validation of configuration objects with detailed error reporting
- **Profile Resolution**: Layered config merging (defaults < profile < file < direct overrides)
- **Environment Integration**: Support for environment-based configuration

### Enhanced Pattern System
- **Pattern Pack v2.0**: Improved default patterns with better accuracy
- **Modular Pattern Loading**: Mix and match pattern packs for custom detection rules
- **Healthcare Patterns**: HIPAA-focused patterns for medical record processing

### Developer Experience
- **Interactive CLI**: `getting-started` command guides new users through setup
- **Better Error Messages**: Clear validation errors and configuration feedback
- **Session Management**: Built-in session cleanup and management commands
- **Comprehensive Testing**: `test` command validates your installation and configuration

---

## 📚 Learn More

* [Workflow Guide](docs/workflows.md)
* [API Reference](docs/api.md)
* [Pattern Pack Guide](docs/patterns.md)
* [Security Practices](docs/security.md)

---

## 🤝 Contributing

We welcome privacy-conscious developers and AI builders!

### Development Setup
```bash
git clone https://github.com/foofork/maskingengine.git
cd maskingengine
pip install -e .[dev]

# Run tests
pytest

# Code quality checks  
black .
flake8 .
mypy maskingengine/
```

### Contribution Guidelines
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### What We're Looking For
- New pattern packs for different industries/regions
- Performance optimizations
- Additional NER model integrations
- Documentation improvements
- Security enhancements

---

## 🔐 License

MIT License. 100% local-first. No data leaves your system.

---