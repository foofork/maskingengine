"""Pattern pack loading and management system for MaskingEngine."""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class PatternRule:
    """Represents a single pattern rule from a YAML pack."""
    name: str
    description: str
    tier: int
    language: str
    country: Optional[str]
    patterns: List[str]
    compiled_patterns: Optional[List[re.Pattern]] = None
    
    def __post_init__(self):
        """Compile regex patterns after initialization."""
        if self.patterns and not self.compiled_patterns:
            self.compiled_patterns = []
            for pattern in self.patterns:
                try:
                    self.compiled_patterns.append(
                        re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                    )
                except re.error as e:
                    print(f"Warning: Invalid regex pattern in {self.name}: {pattern} - {e}")


@dataclass
class PatternPack:
    """Represents a complete pattern pack loaded from YAML."""
    name: str
    description: str
    version: str
    patterns: List[PatternRule]
    
    def get_patterns_by_language(self, language: str = None) -> List[PatternRule]:
        """Get patterns filtered by language."""
        if language is None:
            return self.patterns
        
        return [
            pattern for pattern in self.patterns 
            if pattern.language in ['universal', language]
        ]
    
    def get_patterns_by_tier(self, max_tier: int = None) -> List[PatternRule]:
        """Get patterns filtered by tier (1 = highest priority)."""
        if max_tier is None:
            return self.patterns
        
        return [
            pattern for pattern in self.patterns 
            if pattern.tier <= max_tier
        ]


class PatternPackLoader:
    """Loads and manages YAML pattern packs."""
    
    def __init__(self, patterns_dir: Optional[str] = None):
        """Initialize with patterns directory."""
        if patterns_dir is None:
            # Default to package pattern_packs directory
            package_patterns_dir = Path(__file__).parent / "pattern_packs"
            if package_patterns_dir.exists():
                self.patterns_dir = package_patterns_dir
            else:
                # Fallback to current directory pattern_packs
                self.patterns_dir = Path("pattern_packs")
        else:
            self.patterns_dir = Path(patterns_dir)
            
        self.loaded_packs: Dict[str, PatternPack] = {}
        self.default_pack_name = "default"
        
        # Only try to create directory if it's not a package directory
        if not str(self.patterns_dir).endswith("maskingengine/pattern_packs"):
            try:
                self.patterns_dir.mkdir(exist_ok=True)
            except (PermissionError, OSError) as e:
                print(f"Warning: Cannot create patterns directory {self.patterns_dir}: {e}")
                # Continue with read-only access
    
    def load_pack(self, pack_name: str) -> Optional[PatternPack]:
        """Load a specific pattern pack by name."""
        if pack_name in self.loaded_packs:
            return self.loaded_packs[pack_name]
        
        pack_file = self.patterns_dir / f"{pack_name}.yaml"
        
        if not pack_file.exists():
            print(f"Warning: Pattern pack '{pack_name}' not found at {pack_file}")
            return None
        
        if not pack_file.is_file():
            print(f"Warning: Pattern pack path '{pack_file}' exists but is not a file")
            return None
        
        try:
            with open(pack_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Handle new format with meta section
            if 'meta' in data:
                meta = data['meta']
                pack_name = meta.get('name', pack_name)
                pack_description = meta.get('description', '')
                pack_version = meta.get('version', '1.0.0')
                patterns_data = data.get('patterns', [])
            else:
                # Handle old format (backward compatibility)
                pack_name = data.get('name', pack_name)
                pack_description = data.get('description', '')
                pack_version = data.get('version', '1.0.0')
                patterns_data = data.get('patterns', [])
            
            # Validate required fields
            if not patterns_data:
                print(f"Warning: No patterns found in {pack_file}")
                return None
            
            # Parse pattern rules
            pattern_rules = []
            for pattern_data in patterns_data:
                try:
                    # Handle both old and new pattern formats
                    if 'label' in pattern_data:  # New format
                        rule = PatternRule(
                            name=pattern_data['label'],
                            description=pattern_data.get('description', ''),
                            tier=pattern_data.get('tier', 2),
                            language=pattern_data.get('language', 'universal'),
                            country=pattern_data.get('country'),
                            patterns=[pattern_data['pattern']] if isinstance(pattern_data.get('pattern'), str) else pattern_data.get('patterns', [])
                        )
                    else:  # Old format
                        rule = PatternRule(
                            name=pattern_data['name'],
                            description=pattern_data['description'],
                            tier=pattern_data.get('tier', 2),
                            language=pattern_data.get('language', 'universal'),
                            country=pattern_data.get('country'),
                            patterns=pattern_data['patterns']
                        )
                    pattern_rules.append(rule)
                except (KeyError, TypeError) as e:
                    print(f"Warning: Invalid pattern rule in {pack_file}: {e}")
                    continue
            
            pack = PatternPack(
                name=pack_name,
                description=pack_description,
                version=pack_version,
                patterns=pattern_rules
            )
            
            self.loaded_packs[pack_name] = pack
            return pack
            
        except (yaml.YAMLError, IOError) as e:
            print(f"Error loading pattern pack {pack_file}: {e}")
            return None
    
    def load_packs(self, pack_names: List[str]) -> List[PatternPack]:
        """Load multiple pattern packs."""
        packs = []
        for pack_name in pack_names:
            pack = self.load_pack(pack_name)
            if pack:
                packs.append(pack)
        return packs
    
    def get_combined_patterns(self, pack_names: List[str], language: str = None, max_tier: int = None) -> Dict[str, PatternRule]:
        """Get combined patterns from multiple packs with filtering."""
        combined = {}
        
        # Always include default pack if not explicitly listed
        if self.default_pack_name not in pack_names:
            pack_names = [self.default_pack_name] + pack_names
        
        packs = self.load_packs(pack_names)
        
        for pack in packs:
            patterns = pack.get_patterns_by_language(language)
            if max_tier is not None:
                patterns = [p for p in patterns if p.tier <= max_tier]
            
            for pattern in patterns:
                # Use the pattern name as key, later packs override earlier ones
                combined[pattern.name] = pattern
        
        return combined
    
    def list_available_packs(self) -> List[str]:
        """List all available pattern pack files."""
        if not self.patterns_dir.exists():
            return []
        
        return [
            f.stem for f in self.patterns_dir.glob("*.yaml")
            if f.is_file()
        ]
    
    def validate_pack(self, pack_file: Path) -> Tuple[bool, List[str]]:
        """Validate a pattern pack file and return issues."""
        issues = []
        
        try:
            with open(pack_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except Exception as e:
            return False, [f"Failed to parse YAML: {e}"]
        
        # Handle both new format (with meta) and old format
        if 'meta' in data:
            # New format validation
            meta = data.get('meta', {})
            if not meta.get('name'):
                issues.append("Missing meta.name")
            if not meta.get('description'):
                issues.append("Missing meta.description")
            patterns_data = data.get('patterns', [])
        else:
            # Old format validation
            required_fields = ['name', 'description', 'patterns']
            for field in required_fields:
                if field not in data:
                    issues.append(f"Missing required field: {field}")
            patterns_data = data.get('patterns', [])
        
        # Validate patterns
        if not patterns_data:
            issues.append("No patterns defined")
        elif isinstance(patterns_data, list):
            for i, pattern in enumerate(patterns_data):
                if not isinstance(pattern, dict):
                    issues.append(f"Pattern {i}: Must be a dictionary")
                    continue
                
                # Check for new format (label, pattern) or old format (name, patterns)
                if 'label' in pattern:  # New format
                    if not pattern.get('pattern'):
                        issues.append(f"Pattern {i} ({pattern.get('label', 'unnamed')}): Missing pattern")
                    else:
                        # Validate single regex pattern
                        try:
                            re.compile(pattern['pattern'])
                        except re.error as e:
                            issues.append(f"Pattern {i} ({pattern.get('label', 'unnamed')}) regex: {e}")
                else:  # Old format
                    pattern_required = ['name', 'description', 'patterns']
                    for field in pattern_required:
                        if field not in pattern:
                            issues.append(f"Pattern {i} ({pattern.get('name', 'unnamed')}): Missing {field}")
                    
                    # Validate regex patterns
                    if 'patterns' in pattern:
                        for j, regex_pattern in enumerate(pattern['patterns']):
                            try:
                                re.compile(regex_pattern)
                            except re.error as e:
                                issues.append(f"Pattern {i} ({pattern.get('name', 'unnamed')}) regex {j}: {e}")
        
        return len(issues) == 0, issues


# Context matching removed - all patterns detect without context requirements