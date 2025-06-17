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

### CLI

```bash
echo "Email john@example.com or call 555-123-4567" | maskingengine mask --stdin --regex-only
```

### Python

```python
from maskingengine import Sanitizer

sanitizer = Sanitizer()
masked, mask_map = sanitizer.sanitize("Email john@example.com")
print(masked)  # => Email <<EMAIL_7A9B2C_1>>
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

```python
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

| Mode        | Speed     | When to Use                   |
| ----------- | --------- | ----------------------------- |
| Regex-only  | <50ms     | Logs, structured input, speed |
| Regex + NER | ~200ms    | Unstructured/contextual text  |
| Streaming   | Efficient | Large files, memory-sensitive |

✅ Custom pattern packs supported in all modes.

MaskingEngine is stateless and fast, designed to scale horizontally in microservices or distributed queues.

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

```bash
maskingengine mask input.txt --regex-only -o output.txt
maskingengine mask input.txt --profile healthcare-en
maskingengine getting-started
maskingengine list-profiles
```

---

## 📚 Learn More

* [Workflow Guide](docs/workflows.md)
* [API Reference](docs/api.md)
* [Pattern Pack Guide](docs/patterns.md)
* [Security Practices](docs/security.md)

---

## 🤝 Contributing

1. Fork + clone
2. Add tests
3. Submit a PR

We welcome privacy-conscious developers and AI builders.

---

## 🔐 License

MIT License. 100% local-first. No data leaves your system.

---