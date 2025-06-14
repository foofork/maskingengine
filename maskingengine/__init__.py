"""MaskingEngine: A local-first, privacy-by-design PII sanitizer system."""

__version__ = "1.0.0"

from .sanitizer import Sanitizer
from .config import Config

__all__ = ["Sanitizer", "Config"]