"""Simplified configuration module for minimal architecture."""

class Config:
    """Minimal configuration with pre-defined patterns and hashes."""
    
    # Regex patterns defined inline (no external config)
    PATTERNS = {
        'EMAIL': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        # Comprehensive phone pattern supporting US and major international formats
        'PHONE': r'(?<!\d)(?:\+1[-.\s]?)?\([2-9]\d{2}\)\s?[0-9]\d{2}[-.\s]?\d{4}(?!\d)|\b(?:\+1[-.\s]?)?[2-9]\d{2}[-.\s][0-9]\d{2}[-.\s]\d{4}\b|\b\+(?:44|33|49|81|86|91|61|55|39|34|31|46|47|41|43|32|30)[\s.-]?\d{1,4}[\s.-]?\d{3,4}[\s.-]?\d{3,8}\b',
        'SSN': r'\b\d{3}-\d{2}-\d{4}\b',
        # Improved credit card pattern with major card type prefixes
        'CREDIT_CARD': r'\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6011)(?:[\s-]?\d{4}){3}\b|\b3[47]\d{2}[\s-]?\d{6}[\s-]?\d{5}\b',
        'IPV4': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        'IPV6': r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
    }
    
    # Simple deterministic type mappings for placeholders
    TYPE_HASHES = {
        'EMAIL': '7A9B2C',
        'PHONE': '4D8E1F',
        'SSN': '6C3A9D',
        'CREDIT_CARD': '2F7B8E',
        'PERSON': '9E4C6A',
        'ORGANIZATION': '1B8D3F',
        'ORG': '1B8D3F',  # NER alias
        'LOCATION': '5A2E9C',
        'GPE': '5A2E9C',  # NER alias
        'IPV4': '3C7F2A',
        'IPV6': '8B1E4D'
    }
    
    # Performance settings
    MAX_TEXT_LENGTH = 1_000_000  # 1MB
    NER_ENABLED = True
    NER_MODEL_PATH = "en_core_web_sm"
    
    def __init__(self):
        """Initialize with default settings."""
        pass