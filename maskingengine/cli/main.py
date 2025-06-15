"""MaskingEngine Command Line Interface using Click."""

import json
import sys
from pathlib import Path
from typing import Optional

import click

from maskingengine import Sanitizer, Config, Rehydrator, RehydrationPipeline, RehydrationStorage


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
    help="Content format (auto-detect if not specified)"
)
@click.option(
    "--regex-only",
    is_flag=True,
    help="Use regex-only mode (fastest)"
)
@click.option(
    "--pattern-packs",
    multiple=True,
    help="Custom pattern packs to load"
)
@click.option(
    "--whitelist",
    multiple=True,
    help="Terms to exclude from masking (can be used multiple times)"
)
@click.option(
    "--stdin",
    is_flag=True,
    help="Read input from stdin"
)
def mask(
    input_file: Optional[str],
    output: Optional[str],
    format: Optional[str],
    regex_only: bool,
    pattern_packs: tuple,
    whitelist: tuple,
    stdin: bool
):
    """Mask PII in text, JSON, or HTML content.
    
    Examples:
        echo "Email john@example.com" | maskingengine mask --stdin --regex-only
        maskingengine mask input.txt --regex-only -o output.txt
        maskingengine mask input.txt --pattern-packs custom -o output.txt
        maskingengine mask input.txt --whitelist "support@company.com" -o output.txt
    """
    try:
        # Read input content
        if stdin or input_file is None:
            content = sys.stdin.read().strip()
        else:
            content = Path(input_file).read_text()
        
        # Create configuration
        config = Config(
            pattern_packs=list(pattern_packs) if pattern_packs else ["default"],
            whitelist=list(whitelist) if whitelist else [],
            regex_only=regex_only
        )
        
        # Create sanitizer
        sanitizer = Sanitizer(config)
        
        # Perform sanitization
        masked_content, mask_map = sanitizer.sanitize(content, format=format)
        
        # Write sanitized content
        if output:
            if isinstance(masked_content, dict):
                Path(output).write_text(json.dumps(masked_content, indent=2))
            else:
                Path(output).write_text(str(masked_content))
            click.echo(f"✅ Sanitized content written to: {output}")
        else:
            if isinstance(masked_content, dict):
                click.echo(json.dumps(masked_content, indent=2))
            else:
                click.echo(str(masked_content))
        
        # Display summary
        if mask_map:
            click.echo(f"🔍 Detected {len(mask_map)} PII entities", err=True)
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--session-id",
    help="Session ID for rehydration testing"
)
def test(session_id: Optional[str]):
    """Test MaskingEngine functionality including optional rehydration."""
    click.echo("🧪 Testing MaskingEngine...")
    
    test_content = "Contact John Smith at john@example.com or call 555-123-4567"
    
    try:
        sanitizer = Sanitizer()
        masked_content, mask_map = sanitizer.sanitize(test_content)
        
        click.echo(f"\n📝 Original: {test_content}")
        click.echo(f"🔒 Sanitized: {masked_content}")
        click.echo(f"🔍 Detected {len(mask_map)} PII entities:")
        
        for placeholder, value in mask_map.items():
            click.echo(f"   • {placeholder} → {value}")
        
        # Test rehydration if session_id provided
        if session_id:
            click.echo(f"\n🔄 Testing rehydration with session ID: {session_id}")
            
            # Create rehydration pipeline
            storage = RehydrationStorage()
            pipeline = RehydrationPipeline(sanitizer, storage)
            
            # Store mask map
            storage_path = storage.store_mask_map(session_id, mask_map)
            click.echo(f"💾 Mask map stored at: {storage_path}")
            
            # Test rehydration
            rehydrator = Rehydrator()
            rehydrated_content = rehydrator.rehydrate(masked_content, mask_map)
            
            click.echo(f"🔓 Rehydrated: {rehydrated_content}")
            click.echo(f"✅ Rehydration test: {'PASSED' if rehydrated_content == test_content else 'FAILED'}")
            
            # Cleanup
            storage.delete_mask_map(session_id)
        
        click.echo("\n✅ Test completed! MaskingEngine is working correctly.")
            
    except Exception as e:
        click.echo(f"\n❌ Test failed: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("masked_file", type=click.Path(exists=True))
@click.argument("mask_map_file", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output file path (defaults to stdout)"
)
def rehydrate(masked_file: str, mask_map_file: str, output: Optional[str]):
    """Rehydrate masked content using a stored mask map.
    
    Examples:
        maskingengine rehydrate masked.txt mask_map.json
        maskingengine rehydrate masked.json mask_map.json -o original.json
    """
    try:
        # Read masked content
        masked_content = Path(masked_file).read_text()
        
        # Read mask map
        mask_map = json.loads(Path(mask_map_file).read_text())
        
        # Perform rehydration
        rehydrator = Rehydrator()
        
        # Validate compatibility
        can_rehydrate, issues = rehydrator.check_rehydration_compatibility(masked_content, mask_map)
        if not can_rehydrate:
            click.echo(f"❌ Rehydration compatibility issues:", err=True)
            for issue in issues:
                click.echo(f"   • {issue}", err=True)
            sys.exit(1)
        
        # Rehydrate
        rehydrated_content = rehydrator.rehydrate(masked_content, mask_map)
        
        # Output result
        if output:
            Path(output).write_text(rehydrated_content)
            click.echo(f"✅ Rehydrated content written to: {output}")
        else:
            click.echo(rehydrated_content)
        
        # Show summary
        placeholders_found = len(rehydrator.extract_placeholders(masked_content))
        click.echo(f"🔄 Processed {placeholders_found} placeholders", err=True)
        
    except json.JSONDecodeError as e:
        click.echo(f"❌ Invalid JSON in mask map file: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command(name="session-sanitize")
@click.argument("input_file", type=click.Path(exists=True), required=False)
@click.argument("session_id")
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output file path for sanitized content (defaults to stdout)"
)
@click.option(
    "--mask-map-output",
    type=click.Path(),
    help="Output file path for mask map (defaults to session storage)"
)
@click.option(
    "-f", "--format",
    type=click.Choice(["text", "json", "html"]),
    help="Content format (auto-detect if not specified)"
)
@click.option(
    "--regex-only",
    is_flag=True,
    help="Use regex-only mode (fastest)"
)
@click.option(
    "--pattern-packs",
    multiple=True,
    help="Custom pattern packs to load"
)
@click.option(
    "--whitelist",
    multiple=True,
    help="Terms to exclude from masking"
)
@click.option(
    "--stdin",
    is_flag=True,
    help="Read input from stdin"
)
def session_sanitize(
    input_file: Optional[str],
    session_id: str,
    output: Optional[str],
    mask_map_output: Optional[str],
    format: Optional[str],
    regex_only: bool,
    pattern_packs: tuple,
    whitelist: tuple,
    stdin: bool
):
    """Sanitize content and store mask map for later rehydration.
    
    Examples:
        maskingengine session-sanitize input.txt session123 -o masked.txt
        echo "Email: test@example.com" | maskingengine session-sanitize --stdin session456
    """
    try:
        # Read input content
        if stdin or input_file is None:
            content = sys.stdin.read().strip()
        else:
            content = Path(input_file).read_text()
        
        # Create configuration
        config = Config(
            pattern_packs=list(pattern_packs) if pattern_packs else ["default"],
            whitelist=list(whitelist) if whitelist else [],
            regex_only=regex_only
        )
        
        # Create sanitizer and pipeline
        sanitizer = Sanitizer(config)
        storage = RehydrationStorage()
        pipeline = RehydrationPipeline(sanitizer, storage)
        
        # Perform sanitization with session storage
        masked_content, storage_path = pipeline.sanitize_with_session(
            content, session_id, format
        )
        
        # Write sanitized content
        if output:
            if isinstance(masked_content, dict):
                Path(output).write_text(json.dumps(masked_content, indent=2))
            else:
                Path(output).write_text(str(masked_content))
            click.echo(f"✅ Sanitized content written to: {output}")
        else:
            if isinstance(masked_content, dict):
                click.echo(json.dumps(masked_content, indent=2))
            else:
                click.echo(str(masked_content))
        
        # Optionally export mask map
        if mask_map_output:
            mask_map = storage.load_mask_map(session_id)
            Path(mask_map_output).write_text(json.dumps(mask_map, indent=2))
            click.echo(f"💾 Mask map written to: {mask_map_output}")
        
        # Display summary
        mask_map = storage.load_mask_map(session_id)
        click.echo(f"🔍 Session '{session_id}' created with {len(mask_map)} PII entities", err=True)
        click.echo(f"📁 Mask map stored at: {storage_path}", err=True)
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command(name="session-rehydrate")
@click.argument("masked_file", type=click.Path(exists=True), required=False)
@click.argument("session_id")
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output file path (defaults to stdout)"
)
@click.option(
    "--stdin",
    is_flag=True,
    help="Read masked content from stdin"
)
@click.option(
    "--cleanup",
    is_flag=True,
    help="Delete session after rehydration"
)
def session_rehydrate(
    masked_file: Optional[str],
    session_id: str,
    output: Optional[str],
    stdin: bool,
    cleanup: bool
):
    """Rehydrate content using stored session mask map.
    
    Examples:
        maskingengine session-rehydrate masked.txt session123 -o original.txt
        echo "Email: <<EMAIL_ABC123_1>>" | maskingengine session-rehydrate --stdin session456
    """
    try:
        # Read masked content
        if stdin or masked_file is None:
            masked_content = sys.stdin.read().strip()
        else:
            masked_content = Path(masked_file).read_text()
        
        # Create pipeline
        sanitizer = Sanitizer()
        storage = RehydrationStorage()
        pipeline = RehydrationPipeline(sanitizer, storage)
        
        # Perform rehydration
        rehydrated_content = pipeline.rehydrate_with_session(masked_content, session_id)
        
        if rehydrated_content is None:
            click.echo(f"❌ Session '{session_id}' not found or expired", err=True)
            sys.exit(1)
        
        # Output result
        if output:
            if isinstance(rehydrated_content, dict):
                Path(output).write_text(json.dumps(rehydrated_content, indent=2))
            else:
                Path(output).write_text(str(rehydrated_content))
            click.echo(f"✅ Rehydrated content written to: {output}")
        else:
            if isinstance(rehydrated_content, dict):
                click.echo(json.dumps(rehydrated_content, indent=2))
            else:
                click.echo(str(rehydrated_content))
        
        # Show summary
        rehydrator = Rehydrator()
        placeholders_found = len(rehydrator.extract_placeholders(masked_content))
        click.echo(f"🔄 Processed {placeholders_found} placeholders from session '{session_id}'", err=True)
        
        # Cleanup if requested
        if cleanup:
            success = pipeline.complete_session(session_id)
            if success:
                click.echo(f"🗑️  Session '{session_id}' deleted", err=True)
            else:
                click.echo(f"⚠️  Failed to delete session '{session_id}'", err=True)
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def sessions():
    """List all stored rehydration sessions."""
    try:
        storage = RehydrationStorage()
        session_list = storage.list_sessions()
        
        if not session_list:
            click.echo("📭 No active sessions found")
        else:
            click.echo(f"📋 Found {len(session_list)} active sessions:")
            for session_id in session_list:
                click.echo(f"   • {session_id}")
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command(name="cleanup-sessions")
@click.option(
    "--max-age-hours",
    type=int,
    default=24,
    help="Maximum age in hours before deletion (default: 24)"
)
def cleanup_sessions(max_age_hours: int):
    """Clean up old rehydration sessions."""
    try:
        storage = RehydrationStorage()
        initial_count = len(storage.list_sessions())
        
        storage.cleanup_old_sessions(max_age_hours)
        
        final_count = len(storage.list_sessions())
        deleted_count = initial_count - final_count
        
        click.echo(f"🧹 Cleanup completed: {deleted_count} sessions deleted, {final_count} remaining")
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()