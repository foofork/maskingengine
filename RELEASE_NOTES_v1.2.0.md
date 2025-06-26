# MaskingEngine v1.2.0 - Configuration Profiles & Cross-Platform Fixes 🚀

We're excited to announce MaskingEngine v1.2.0 with enhanced configuration management and improved cross-platform compatibility!

## 📦 Installation

```bash
pip install maskingengine==1.2.0
```

## ✨ What's New

### Configuration Profiles
Pre-configured profiles make it easier to get started with common use cases:

```bash
# Use minimal profile for fastest performance (regex-only)
maskingengine mask input.txt --profile minimal

# Healthcare-focused configuration
maskingengine mask patient-data.txt --profile healthcare-en

# High-security mode for maximum detection
maskingengine mask sensitive.txt --profile high-security
```

Available profiles:
- **minimal**: Regex-only mode for <50ms performance
- **standard**: Balanced regex + NER detection
- **healthcare-en**: Healthcare-focused patterns (HIPAA-relevant)
- **high-security**: Maximum detection with lower confidence thresholds

### Cross-Platform Improvements
- Fixed Unicode encoding issues on Windows
- Resolved GitHub Actions test failures across all platforms
- Optimized CI/CD test matrix for faster releases

### API Enhancements
```python
from maskingengine import Sanitizer, Config
from maskingengine.core import ConfigResolver

# Use configuration profiles programmatically
resolver = ConfigResolver()
result = resolver.resolve_and_validate(profile='healthcare-en')
config = Config(**result['resolved_config'])
sanitizer = Sanitizer(config)
```

## 🐛 Bug Fixes
- Fixed `Sanitizer(profile='minimal')` parameter usage
- Resolved PyPI packaging issues for Python 3.8
- Corrected mypy type checking errors
- Fixed test compatibility across Python 3.8-3.12

## 📈 Performance
- Maintained <50ms regex-only processing
- Reduced CI/CD build times by 70%
- Optimized test suite execution

## 🙏 Acknowledgments
Thank you to our contributors and users who reported issues and helped improve MaskingEngine!

## 📚 Resources
- **Documentation**: https://github.com/foofork/maskingengine/tree/main/docs
- **PyPI Package**: https://pypi.org/project/maskingengine/
- **GitHub Repository**: https://github.com/foofork/maskingengine
- **Issue Tracker**: https://github.com/foofork/maskingengine/issues

---

**Upgrade today and enjoy improved configuration management!**

```bash
pip install --upgrade maskingengine
```