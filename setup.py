"""Setup configuration for MaskingEngine package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read version from package
version_path = Path(__file__).parent / "maskingengine" / "__init__.py"
version = "1.0.0"
if version_path.exists():
    for line in version_path.read_text().splitlines():
        if line.startswith("__version__"):
            version = line.split('"')[1]
            break

setup(
    name="maskingengine",
    version=version,
    author="MaskingEngine Team",
    author_email="contact@maskingengine.dev",
    description="Privacy-first, blazing-fast PII redaction for AI pipelines",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/foofork/maskingengine",
    project_urls={
        "Bug Reports": "https://github.com/foofork/maskingengine/issues",
        "Source": "https://github.com/foofork/maskingengine",
        "Documentation": "https://github.com/foofork/maskingengine/blob/main/docs/README.md",
    },
    packages=find_packages(exclude=["tests", "tests.*", "docs", "examples"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security",
        "Topic :: Text Processing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "transformers>=4.21.0",
        "torch>=1.12.0",
        "click>=8.0.0",
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "pydantic>=1.8.0",
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.910",
            "pre-commit>=2.15",
        ],
        "api": [
            "fastapi>=0.68.0",
            "uvicorn>=0.15.0",
        ],
        "full": [
            "transformers>=4.21.0",
            "torch>=1.12.0",
            "fastapi>=0.68.0",
            "uvicorn>=0.15.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "maskingengine=maskingengine.cli.main:cli",
        ],
    },
    package_data={
        "maskingengine": [
            "patterns/*.yaml",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="pii, privacy, redaction, sanitization, ai, nlp, security, data-protection",
)