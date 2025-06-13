"""MaskingEngine: A local-first, privacy-by-design PII sanitizer system."""

__version__ = "1.0.0"

from .core.sanitizer import sanitize, rehydrate
from .core.config import SanitizerConfig

__all__ = ["sanitize", "rehydrate", "SanitizerConfig"]