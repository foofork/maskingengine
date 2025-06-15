"""Simplified configuration module for minimal architecture."""

import os
from pathlib import Path

class Config:
    """Configuration with pure YAML-based pattern pack system."""
    
    # Simple deterministic type mappings for placeholders
    TYPE_HASHES = {
        'EMAIL': '7A9B2C',
        'EMAIL_ADDRESS': '7A9B2C',
        'PHONE': '4D8E1F',
        'US_PHONE': '4D8E1F',
        'FR_PHONE_NUMBER': '4D8E1F',
        'INTERNATIONAL_PHONE': '4D8E1F',
        'SSN': '6C3A9D',
        'US_SSN': '6C3A9D',
        'CREDIT_CARD': '2F7B8E',
        'CREDIT_CARD_NUMBER': '2F7B8E',
        'PERSON': '9E4C6A',
        'ORGANIZATION': '1B8D3F',
        'ORG': '1B8D3F',  # NER alias
        'LOCATION': '5A2E9C',
        'GPE': '5A2E9C',  # NER alias
        'IPV4': '3C7F2A',
        'IPV4_ADDRESS': '3C7F2A',
        'IPV6': '8B1E4D',
        'IPV6_ADDRESS': '8B1E4D',
        'DATE': '8F2A1C',
        'TIME': '3E9B4F',
        # Country-specific IDs
        'ES_NATIONAL_ID': 'A1B2C3',
        'DE_TAX_ID': 'D4E5F6',
        'FR_SOCIAL_SECURITY': 'F7G8H9',
        'UK_NATIONAL_INSURANCE': 'U1K2N3',
        'CA_SOCIAL_INSURANCE': 'C4A5N6',
        # Custom enterprise patterns
        'EMPLOYEE_ID': 'E1D2F3',
        'PROJECT_CODE': 'P4R5J6',
        'CUSTOMER_ID': 'C7U8S9',
        'API_KEY': 'A0P1I2'
    }
    
    # Performance settings
    MAX_TEXT_LENGTH = 1_000_000  # 1MB
    NER_ENABLED = True
    NER_MODEL_PATH = "yonigo/distilbert-base-multilingual-cased-pii"
    NER_MIN_CONFIDENCE = 0.5
    
    def __init__(
        self, 
        pattern_packs: list = None,
        whitelist: list = None,
        placeholder_prefix: str = "<<",
        min_confidence: float = None,
        strict_validation: bool = True,
        regex_only: bool = False
    ):
        """Initialize configuration with customizable options."""
        # Pattern pack configuration
        self.pattern_packs = pattern_packs or ["default"]
        
        # Determine patterns directory - use package patterns if installed, otherwise local
        package_patterns_dir = Path(__file__).parent / "patterns"
        if package_patterns_dir.exists():
            self.patterns_dir = str(package_patterns_dir)
        else:
            self.patterns_dir = "patterns"
        
        # Detection configuration
        self.whitelist = set(whitelist) if whitelist else set()
        self.placeholder_prefix = placeholder_prefix
        self.strict_validation = strict_validation
        
        # NER configuration  
        if regex_only:
            self.NER_ENABLED = False
        if min_confidence is not None:
            self.NER_MIN_CONFIDENCE = min_confidence
        
        # Build combined patterns from packs
        self.PATTERNS = self._build_patterns()
    
    def _build_patterns(self):
        """Build regex patterns purely from YAML pattern packs."""
        combined_patterns = {}
        
        try:
            from .pattern_packs import PatternPackLoader
            loader = PatternPackLoader(self.patterns_dir)
            
            # Load specified pattern packs
            pack_patterns = loader.get_combined_patterns(self.pattern_packs)
            
            # Convert pattern pack rules to simple regex dict
            for rule_name, rule in pack_patterns.items():
                if rule.compiled_patterns:
                    # Store all patterns for this rule
                    combined_patterns[rule_name] = rule.patterns
                    
        except (ImportError, Exception) as e:
            print(f"Warning: Could not load pattern packs: {e}")
            # If pattern packs fail to load, we have no fallback patterns
            print("No patterns loaded - all detection will be disabled!")
            
        return combined_patterns