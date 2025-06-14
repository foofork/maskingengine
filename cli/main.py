"""MaskingEngine Command Line Interface using Click."""

import json
import sys
from pathlib import Path
from typing import Optional, Set

import click

from maskingengine import sanitize, rehydrate
from maskingengine.core.config import SanitizerConfig


@click.group()
@click.version_option(version="1.0.0", prog_name="maskingengine")
def cli():
    """MaskingEngine CLI - Local-first PII sanitization tool."""
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True), required=False)
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output file path (defaults to stdout)"
)
@click.option(
    "-f", "--format",
    type=click.Choice(["text", "json", "html"]),
    default="text",
    help="Content format (default: text)"
)
@click.option(
    "-m", "--mask-map",
    type=click.Path(),
    help="Save mask map to JSON file"
)
@click.option(
    "--min-confidence",
    type=float,
    default=0.7,
    help="Minimum confidence threshold (0.0-1.0)"
)
@click.option(
    "--placeholder-prefix",
    default="MASKED_",
    help="Prefix for masked placeholders"
)
@click.option(
    "--whitelist",
    multiple=True,
    help="Terms to exclude from masking (can be used multiple times)"
)
@click.option(
    "--no-ner",
    is_flag=True,
    help="Disable NER-based detection"
)
@click.option(
    "--no-regex",
    is_flag=True,
    help="Disable regex-based detection"
)
@click.option(
    "--stdin",
    is_flag=True,
    help="Read input from stdin"
)
def mask(
    input_file: Optional[str],
    output: Optional[str],
    format: str,
    mask_map: Optional[str],
    min_confidence: float,
    placeholder_prefix: str,
    whitelist: tuple,
    no_ner: bool,
    no_regex: bool,
    stdin: bool
):
    """Mask PII in text, JSON, or HTML content.
    
    Examples:
        maskingengine mask input.txt -o output.txt
        maskingengine mask -f json data.json -m masks.json
        echo "Call me at 555-1234" | maskingengine mask --stdin
    """
    try:
        # Read input content
        if stdin or input_file is None:
            content = sys.stdin.read()
        else:
            content = Path(input_file).read_text()
        
        # Create configuration
        config = SanitizerConfig(
            min_confidence=min_confidence,
            whitelist=set(whitelist) if whitelist else None,
            placeholder_prefix=placeholder_prefix,
            enable_ner=not no_ner,
            enable_regex=not no_regex,
        )
        
        # Perform sanitization
        result = sanitize(content, format=format, config=config)
        
        # Write sanitized content
        if output:
            Path(output).write_text(result.sanitized_content)
            click.echo(f"✅ Sanitized content written to: {output}")
        else:
            click.echo(result.sanitized_content)
        
        # Save mask map if requested
        if mask_map:
            Path(mask_map).write_text(
                json.dumps(result.mask_map, indent=2)
            )
            click.echo(f"💾 Mask map saved to: {mask_map}")
        
        # Display summary
        click.echo(f"🔍 Detected {len(result.mask_map)} PII entities", err=True)
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True), required=False)
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output file path (defaults to stdout)"
)
@click.option(
    "-f", "--format",
    type=click.Choice(["text", "json", "html"]),
    default="text",
    help="Content format (default: text)"
)
@click.option(
    "-m", "--mask-map",
    type=click.Path(exists=True),
    required=True,
    help="JSON file containing mask mappings"
)
@click.option(
    "--stdin",
    is_flag=True,
    help="Read input from stdin"
)
def unmask(
    input_file: Optional[str],
    output: Optional[str],
    format: str,
    mask_map: str,
    stdin: bool
):
    """Unmask (rehydrate) previously sanitized content.
    
    Examples:
        maskingengine unmask output.txt -m masks.json -o restored.txt
        maskingengine unmask -f json sanitized.json -m masks.json
    """
    try:
        # Read input content
        if stdin or input_file is None:
            content = sys.stdin.read()
        else:
            content = Path(input_file).read_text()
        
        # Load mask map
        mask_map_data = json.loads(Path(mask_map).read_text())
        
        # Perform rehydration
        original_content = rehydrate(
            sanitized_content=content,
            mask_map=mask_map_data,
            format=format
        )
        
        # Write restored content
        if output:
            Path(output).write_text(original_content)
            click.echo(f"✅ Restored content written to: {output}")
        else:
            click.echo(original_content)
        
        # Display summary
        click.echo(f"♻️  Restored {len(mask_map_data)} placeholders", err=True)
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--enable-ner/--disable-ner",
    default=True,
    help="Test NER model availability"
)
def test(enable_ner: bool):
    """Test MaskingEngine functionality."""
    click.echo("🧪 Testing MaskingEngine...")
    
    test_content = "Contact John Doe at john.doe@example.com or call 555-1234-5678"
    
    try:
        config = SanitizerConfig(enable_ner=enable_ner)
        result = sanitize(test_content, config=config)
        
        click.echo(f"\n📝 Original: {test_content}")
        click.echo(f"🔒 Sanitized: {result.sanitized_content}")
        click.echo(f"🔍 Detected {len(result.mask_map)} PII entities:")
        
        for placeholder, value in result.mask_map.items():
            click.echo(f"   • {placeholder} → {value}")
        
        # Test rehydration
        restored = rehydrate(result.sanitized_content, result.mask_map)
        click.echo(f"\n♻️  Restored: {restored}")
        
        if restored == test_content:
            click.echo("\n✅ Test passed! Sanitization and rehydration working correctly.")
        else:
            click.echo("\n❌ Test failed! Content not properly restored.")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"\n❌ Test failed: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()