# MaskingEngine v1.0.0 - Now Available on PyPI! 🎉

We're excited to announce that MaskingEngine is now available on PyPI!

## 📦 Installation

```bash
pip install maskingengine
```

## 🚀 What's Included

### Core Features
- **Dual Detection Engines**: Lightning-fast regex patterns + context-aware NER (DistilBERT)
- **Multilingual Support**: PII detection in 100+ languages
- **Deterministic Masking**: Consistent placeholder generation with `<<TYPE_HASH_INDEX>>` format
- **Rehydration System**: Optional restoration of original PII for AI pipelines
- **Format Preservation**: Maintains structure in JSON, HTML, and plain text
- **YAML Pattern Packs**: Easily extensible detection patterns

### Interfaces
- **Python SDK**: Simple, intuitive API for integration
- **CLI Tool**: Command-line interface for scripts and automation
- **REST API**: FastAPI-powered server for microservices

### Performance
- **Regex-only mode**: <50ms for structured PII
- **NER + Regex**: <200ms after model loading (8s first run)
- **Production-ready**: Comprehensive error handling and logging

## 📝 Quick Start

```python
from maskingengine import Sanitizer

sanitizer = Sanitizer()
masked, mask_map = sanitizer.sanitize("Contact john@example.com")
print(masked)  # Contact <<EMAIL_7A9B2C_1>>
```

## 🔗 Resources

- **Documentation**: https://github.com/foofork/maskingengine/tree/main/docs
- **PyPI Package**: https://pypi.org/project/maskingengine/
- **GitHub Repository**: https://github.com/foofork/maskingengine
- **Issue Tracker**: https://github.com/foofork/maskingengine/issues

## 🙏 Acknowledgments

Thank you to everyone who contributed to making this release possible!

## 📈 What's Next

- Additional language-specific pattern packs
- Performance optimizations for large-scale processing
- Enhanced LLM integration examples
- Community-contributed patterns

---

**Install it today and let us know what you think!**

```bash
pip install maskingengine
```