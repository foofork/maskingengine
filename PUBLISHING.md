# Publishing MaskingEngine to PyPI

This guide covers how to make MaskingEngine pip-installable for developers.

## ✅ Current Status

Your package is **already well-structured** for PyPI distribution! Here's what you have:

### Package Structure ✅
- ✅ Proper `pyproject.toml` and `setup.py` configuration
- ✅ Correct package directory structure (`maskingengine/`)
- ✅ Entry points for CLI commands (`maskingengine` command)
- ✅ Package data inclusion (YAML pattern files)
- ✅ Proper dependency specification
- ✅ MIT license
- ✅ Comprehensive README.md

### Distribution Files ✅
- ✅ `maskingengine-1.0.0-py3-none-any.whl` (wheel package)
- ✅ `maskingengine-1.0.0.tar.gz` (source distribution)

## 🚀 Publishing Steps

### 1. Test Local Installation

```bash
# Create test environment
python3 -m venv test-env
source test-env/bin/activate

# Install from wheel
pip install dist/maskingengine-1.0.0-py3-none-any.whl

# Test installation
maskingengine test
python -c "from maskingengine import Sanitizer; print('✅ Installation works!')"

# Cleanup
deactivate
rm -rf test-env
```

### 2. Prepare for PyPI

#### Option A: TestPyPI (Recommended First)
```bash
# Activate build environment
source build-env/bin/activate

# Upload to TestPyPI
twine upload --repository testpypi dist/*
```

#### Option B: Real PyPI
```bash
# Upload to real PyPI
twine upload dist/*
```

### 3. PyPI Account Setup

1. **Create PyPI account**: https://pypi.org/account/register/
2. **Create TestPyPI account**: https://test.pypi.org/account/register/
3. **Generate API tokens** for both accounts
4. **Configure authentication**:
   ```bash
   # Create ~/.pypirc
   cat > ~/.pypirc << EOF
   [distutils]
   index-servers =
       pypi
       testpypi

   [pypi]
   username = __token__
   password = <your-pypi-token>

   [testpypi]
   repository = https://test.pypi.org/legacy/
   username = __token__
   password = <your-testpypi-token>
   EOF
   ```

## 📦 What Developers Get

Once published, developers can install with:

```bash
# Basic installation
pip install maskingengine

# With API support
pip install maskingengine[api]

# Development installation
pip install maskingengine[dev]

# Minimal installation (regex-only)
pip install maskingengine[minimal]
```

## 🔧 Developer Experience Features

### 1. Easy CLI Access ✅
```bash
# Works immediately after pip install
maskingengine mask "email@example.com" --regex-only
```

### 2. Import-Ready ✅
```python
from maskingengine import Sanitizer, Config
# No additional setup needed
```

### 3. Pattern Packs Included ✅
```python
# Built-in patterns work out of the box
sanitizer = Sanitizer()  # Uses default patterns
```

### 4. Optional Dependencies ✅
```python
# Developers can choose their installation level
pip install maskingengine[minimal]  # Just regex patterns
pip install maskingengine[api]      # + REST API
pip install maskingengine[dev]      # + development tools
```

## 🛠 Maintenance Commands

### Update Version
```bash
# Update version in pyproject.toml and __init__.py
# Then rebuild
python -m build
```

### Test Package
```bash
# Check package
twine check dist/*

# Test upload to TestPyPI
twine upload --repository testpypi dist/*
```

### Publishing Workflow
```bash
# 1. Update version
# 2. Rebuild packages
rm -rf dist/ build/
python -m build

# 3. Test locally
pip install dist/*.whl

# 4. Upload to TestPyPI first
twine upload --repository testpypi dist/*

# 5. Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ maskingengine

# 6. If all good, upload to real PyPI
twine upload dist/*
```

## 📋 Final Checklist

### Before Publishing ✅
- ✅ Package builds successfully (`python -m build`)
- ✅ Local installation works (`pip install dist/*.whl`)
- ✅ CLI commands work (`maskingengine test`)
- ✅ All tests pass (`pytest`)
- ✅ Documentation is complete
- ✅ Version number is updated
- ✅ GitHub URLs are correct

### After Publishing
- [ ] Test installation from PyPI: `pip install maskingengine`
- [ ] Update README to remove "install from source" notice
- [ ] Create GitHub release tag
- [ ] Update documentation with PyPI installation

## 🎯 Key Benefits for Developers

1. **One-Command Install**: `pip install maskingengine`
2. **Immediate CLI Access**: `maskingengine` command available globally
3. **Zero Configuration**: Works out of the box with sensible defaults
4. **Optional Features**: Install only what you need
5. **Standard Python Package**: Follows all Python packaging best practices
6. **Cross-Platform**: Works on Windows, macOS, Linux
7. **Virtual Environment Friendly**: Installs cleanly in any environment

## 🚨 Important Notes

1. **Package Name**: `maskingengine` (check availability on PyPI first)
2. **Versioning**: Use semantic versioning (1.0.0, 1.0.1, etc.)
3. **Dependencies**: All required packages are specified
4. **License**: MIT license included
5. **Documentation**: Complete docs in `docs/` directory

Your package is **production-ready** for PyPI distribution!