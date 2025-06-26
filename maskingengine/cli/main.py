"""MaskingEngine Command Line Interface using Click."""

import json
import sys
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

import click

from maskingengine import Sanitizer, Config, Rehydrator, RehydrationPipeline, RehydrationStorage
from maskingengine.core import ConfigResolver
from maskingengine.pipeline import StreamingMaskingSession, StreamingTextProcessor


@click.group()
@click.version_option(version="1.2.0", prog_name="maskingengine")
def cli() -> None:
    """MaskingEngine CLI - Local-first PII sanitization tool.

    Quick Start:
        New user? Run: maskingengine getting-started

        Or jump right in:
        1. List available profiles: maskingengine list-profiles
        2. Test with sample text: maskingengine test-sample "Email: john@example.com" --profile minimal
        3. Mask your content: maskingengine mask input.txt --profile healthcare-en -o output.txt

    Command Groups:
        Getting Started:   getting-started
        Core Commands:     mask, test-sample
        Discovery:         list-profiles, list-packs, list-models
        Configuration:     validate-config
        Sessions:          session-sanitize, session-rehydrate, sessions, cleanup-sessions
        Rehydration:       rehydrate
        Testing:           test
    """
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True), required=False)
@click.option("-o", "--output", type=click.Path(), help="Output file path (defaults to stdout)")
@click.option(
    "-f",
    "--format",
    type=click.Choice(["text", "json", "html"]),
    help="Content format (auto-detect if not specified)",
)
@click.option("--regex-only", is_flag=True, help="Use regex-only mode (fastest)")
@click.option("--pattern-packs", multiple=True, help="Custom pattern packs to load")
@click.option(
    "--whitelist", multiple=True, help="Terms to exclude from masking (can be used multiple times)"
)
@click.option("--stdin", is_flag=True, help="Read input from stdin")
@click.option("--profile", help="Use a predefined configuration profile")
def mask(
    input_file: Optional[str],
    output: Optional[str],
    format: Optional[str],
    regex_only: bool,
    pattern_packs: tuple,
    whitelist: tuple,
    stdin: bool,
    profile: Optional[str],
) -> None:
    """Mask PII in text, JSON, or HTML content.

    Examples:
        echo "Email john@example.com" | maskingengine mask --stdin --regex-only
        maskingengine mask input.txt --regex-only -o output.txt
        maskingengine mask input.txt --pattern-packs custom -o output.txt
        maskingengine mask input.txt --pattern-packs default --pattern-packs healthcare -o output.txt
        maskingengine mask input.txt --profile healthcare-en -o output.txt
        maskingengine mask input.txt --whitelist "support@company.com" -o output.txt
    """
    try:
        # Read input content
        if stdin or input_file is None:
            content = sys.stdin.read().strip()
        else:
            content = Path(input_file).read_text()

        # Create configuration
        if profile:
            # Use ConfigResolver for profile-based configuration
            resolver = ConfigResolver()

            # Build user config from CLI overrides
            user_config: Dict[str, Any] = {}
            if pattern_packs:
                user_config["regex_packs"] = list(pattern_packs)
            if whitelist:
                user_config["whitelist"] = list(whitelist)
            if regex_only:
                user_config["regex_only"] = True

            # Resolve configuration
            result = resolver.resolve_and_validate(
                config=user_config if user_config else None, profile=profile
            )

            if result["status"] != "valid":
                click.echo("❌ Configuration is invalid:", err=True)
                for issue in result["issues"]:
                    click.echo(f"   • {issue}", err=True)
                sys.exit(1)

            # Create Config object from resolved config
            config_dict = result["resolved_config"].copy()
            # Map regex_packs to pattern_packs for Config constructor
            if "regex_packs" in config_dict:
                config_dict["pattern_packs"] = config_dict.pop("regex_packs")

            config = Config(
                **{
                    k: v
                    for k, v in config_dict.items()
                    if k
                    in [
                        "pattern_packs",
                        "regex_only",
                        "whitelist",
                        "strict_validation",
                        "min_confidence",
                    ]
                }
            )
        else:
            # Direct configuration without profile
            config = Config(
                pattern_packs=list(pattern_packs) if pattern_packs else ["default"],
                whitelist=list(whitelist) if whitelist else [],
                regex_only=regex_only,
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
@click.option("--session-id", help="Session ID for rehydration testing")
def test(session_id: Optional[str]) -> None:
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
            click.echo(
                f"✅ Rehydration test: {'PASSED' if rehydrated_content == test_content else 'FAILED'}"
            )

            # Cleanup
            storage.delete_mask_map(session_id)

        click.echo("\n✅ Test completed! MaskingEngine is working correctly.")

    except Exception as e:
        click.echo(f"\n❌ Test failed: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("masked_file", type=click.Path(exists=True))
@click.argument("mask_map_file", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), help="Output file path (defaults to stdout)")
def rehydrate(masked_file: str, mask_map_file: str, output: Optional[str]) -> None:
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
            if isinstance(rehydrated_content, dict):
                Path(output).write_text(json.dumps(rehydrated_content, indent=2))
            else:
                Path(output).write_text(str(rehydrated_content))
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
    "-o",
    "--output",
    type=click.Path(),
    help="Output file path for sanitized content (defaults to stdout)",
)
@click.option(
    "--mask-map-output",
    type=click.Path(),
    help="Output file path for mask map (defaults to session storage)",
)
@click.option(
    "-f",
    "--format",
    type=click.Choice(["text", "json", "html"]),
    help="Content format (auto-detect if not specified)",
)
@click.option("--regex-only", is_flag=True, help="Use regex-only mode (fastest)")
@click.option("--pattern-packs", multiple=True, help="Custom pattern packs to load")
@click.option("--whitelist", multiple=True, help="Terms to exclude from masking")
@click.option("--stdin", is_flag=True, help="Read input from stdin")
def session_sanitize(
    input_file: Optional[str],
    session_id: str,
    output: Optional[str],
    mask_map_output: Optional[str],
    format: Optional[str],
    regex_only: bool,
    pattern_packs: tuple,
    whitelist: tuple,
    stdin: bool,
) -> None:
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
            regex_only=regex_only,
        )

        # Create sanitizer and pipeline
        sanitizer = Sanitizer(config)
        storage = RehydrationStorage()
        pipeline = RehydrationPipeline(sanitizer, storage)

        # Perform sanitization with session storage
        masked_content, storage_path = pipeline.sanitize_with_session(content, session_id, format)

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
            if mask_map:
                Path(mask_map_output).write_text(json.dumps(mask_map, indent=2))
                click.echo(f"💾 Mask map written to: {mask_map_output}")
            else:
                click.echo(f"⚠️  Warning: No mask map found for session '{session_id}'", err=True)

        # Display summary
        mask_map = storage.load_mask_map(session_id)
        entity_count = len(mask_map) if mask_map else 0
        click.echo(f"🔍 Session '{session_id}' created with {entity_count} PII entities", err=True)
        click.echo(f"📁 Mask map stored at: {storage_path}", err=True)

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command(name="session-rehydrate")
@click.argument("masked_file", type=click.Path(exists=True), required=False)
@click.argument("session_id")
@click.option("-o", "--output", type=click.Path(), help="Output file path (defaults to stdout)")
@click.option("--stdin", is_flag=True, help="Read masked content from stdin")
@click.option("--cleanup", is_flag=True, help="Delete session after rehydration")
def session_rehydrate(
    masked_file: Optional[str], session_id: str, output: Optional[str], stdin: bool, cleanup: bool
) -> None:
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
        click.echo(
            f"🔄 Processed {placeholders_found} placeholders from session '{session_id}'", err=True
        )

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
def sessions() -> None:
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
    help="Maximum age in hours before deletion (default: 24)",
)
def cleanup_sessions(max_age_hours: int) -> None:
    """Clean up old rehydration sessions."""
    try:
        storage = RehydrationStorage()
        initial_count = len(storage.list_sessions())

        storage.cleanup_old_sessions(max_age_hours)

        final_count = len(storage.list_sessions())
        deleted_count = initial_count - final_count

        click.echo(
            f"🧹 Cleanup completed: {deleted_count} sessions deleted, {final_count} remaining"
        )

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command(name="validate-config")
@click.argument("config_file", type=click.Path(exists=True), required=False)
@click.option("--profile", help="Validate with a specific profile")
def validate_config(config_file: Optional[str], profile: Optional[str]) -> None:
    """Validate configuration file or current configuration.

    Examples:
        maskingengine validate-config config.yaml
        maskingengine validate-config --profile healthcare-en
    """
    try:
        resolver = ConfigResolver()

        # Load user config if provided
        user_config = {}
        if config_file:
            with open(config_file, "r") as f:
                if config_file.endswith(".json"):
                    user_config = json.load(f)
                else:
                    user_config = yaml.safe_load(f) or {}

        # Resolve and validate
        result = resolver.resolve_and_validate(
            config=user_config if user_config else None, profile=profile
        )

        # Display results
        if result["status"] == "valid":
            click.echo("✅ Configuration is valid")
            click.echo(f"📄 {result['explanation']}")

            if result["issues"]:
                click.echo("\n⚠️  Warnings:")
                for issue in result["issues"]:
                    if issue.startswith("Warning:"):
                        click.echo(f"   • {issue}")
        else:
            click.echo("❌ Configuration is invalid")
            click.echo(f"📄 {result['explanation']}")

            if result["issues"]:
                click.echo("\n🚨 Issues:")
                for issue in result["issues"]:
                    click.echo(f"   • {issue}")

            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command(name="list-models")
def list_models() -> None:
    """List available NER models from the model registry."""
    try:
        # Look for models.yaml in core config directory
        models_file = Path(__file__).parent.parent / "core" / "models.yaml"
        if not models_file.exists():
            click.echo("📭 No model registry found (models.yaml)")
            return

        with open(models_file, "r") as f:
            models_data = yaml.safe_load(f) or {}

        models = models_data.get("models", [])
        if not models:
            click.echo("📭 No models registered")
            return

        click.echo(f"🤖 Found {len(models)} registered models:\n")

        for model in models:
            click.echo(f"• {model['id']} ({model.get('name', 'No name')})")
            click.echo(f"  Type: {model.get('type', 'unknown')}")
            click.echo(f"  Languages: {', '.join(model.get('languages', []))}")
            click.echo(f"  Entities: {', '.join(model.get('supported_entities', []))}")
            if model.get("description"):
                click.echo(f"  Description: {model['description']}")
            click.echo()

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command(name="list-packs")
def list_packs() -> None:
    """List available pattern packs."""
    try:
        from maskingengine.pattern_packs import PatternPackLoader

        # Use package pattern_packs directory
        loader = PatternPackLoader()  # PatternPackLoader defaults to package location
        packs = loader.list_available_packs()

        if packs:
            click.echo(f"📦 Found {len(packs)} pattern packs:\n")

            for pack_name in sorted(packs):
                pack = loader.load_pack(pack_name)
                if pack:
                    click.echo(f"• {pack.name} (v{pack.version})")
                    click.echo(f"  Description: {pack.description}")
                    click.echo(f"  Patterns: {len(pack.patterns)}")
                    click.echo()
                else:
                    click.echo(f"• {pack_name} (failed to load)")
        else:
            click.echo("📭 No pattern packs found")

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command(name="test-sample")
@click.argument("sample_text")
@click.option("--config", type=click.Path(exists=True), help="Path to configuration file")
@click.option("--profile", help="Use a predefined configuration profile")
@click.option("--regex-only", is_flag=True, help="Use regex-only mode")
def test_sample(
    sample_text: str, config: Optional[str], profile: Optional[str], regex_only: bool
) -> None:
    """Test masking on a sample text string.

    Examples:
        maskingengine test-sample "Email john@example.com for details"
        maskingengine test-sample "Call 555-123-4567" --profile minimal
    """
    try:
        # Resolve configuration
        resolver = ConfigResolver()

        # Load user config if provided
        user_config = {}
        if config:
            with open(config, "r") as f:
                if config.endswith(".json"):
                    user_config = json.load(f)
                else:
                    user_config = yaml.safe_load(f) or {}

        # Add CLI overrides
        if regex_only:
            user_config["regex_only"] = True

        # Resolve configuration
        result = resolver.resolve_and_validate(
            config=user_config if user_config else None, profile=profile
        )

        if result["status"] != "valid":
            click.echo("❌ Configuration is invalid:")
            for issue in result["issues"]:
                click.echo(f"   • {issue}")
            sys.exit(1)

        # Create sanitizer with resolved config
        config_dict = result["resolved_config"].copy()
        # Map regex_packs to pattern_packs for Config constructor
        if "regex_packs" in config_dict:
            config_dict["pattern_packs"] = config_dict.pop("regex_packs")

        config_obj = Config(
            **{
                k: v
                for k, v in config_dict.items()
                if k in ["pattern_packs", "regex_only", "whitelist", "strict_validation"]
            }
        )

        sanitizer = Sanitizer(config_obj)

        # Process sample
        masked_content, mask_map = sanitizer.sanitize(sample_text)

        # Display results
        click.echo(f"📝 Original: {sample_text}")
        click.echo(f"🔒 Masked:   {masked_content}")

        if mask_map:
            click.echo(f"\n🔍 Detected {len(mask_map)} PII entities:")
            for placeholder, value in mask_map.items():
                click.echo(f"   • {placeholder} → {value}")
        else:
            click.echo("\n✅ No PII detected")

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command(name="getting-started")
def getting_started() -> None:
    """Interactive guide to get started with MaskingEngine."""
    click.echo("🚀 Welcome to MaskingEngine - Local-first PII Sanitization")
    click.echo("=" * 60)

    click.echo("\n📋 Step 1: Available Configuration Profiles")
    click.echo("Choose a profile based on your use case:\n")

    profiles_info = {
        "minimal": "⚡ Fastest - Regex-only detection for basic PII (emails, phones)",
        "standard": "⚖️  Balanced - Regex + AI detection for comprehensive coverage",
        # "healthcare-en": "🏥 Healthcare - HIPAA-focused patterns for medical data",
        # Commented out as these are now examples only
        # "finance-en": "💰 Finance - Financial PII patterns (SSN, credit cards)",
        "high-security": "🔒 Maximum - All available patterns and models",
    }

    for profile, desc in profiles_info.items():
        click.echo(f"  • {profile:<15} {desc}")

    click.echo(f"\n📖 Step 2: Test with Sample Data")
    click.echo("Try masking some sample text:")
    click.echo('  maskingengine test-sample "Contact john@example.com" --profile minimal')

    click.echo(f"\n🔧 Step 3: Mask Your Content")
    click.echo("Mask your files or stdin:")
    click.echo("  maskingengine mask input.txt --profile healthcare-en -o output.txt")
    click.echo('  echo "Email: test@example.com" | maskingengine mask --stdin --profile minimal')

    click.echo(f"\n🔍 Step 4: Explore Available Resources")
    click.echo("Discover what's available:")
    click.echo("  maskingengine list-profiles    # Configuration profiles")
    click.echo("  maskingengine list-packs       # Pattern packs")
    click.echo("  maskingengine list-models      # NER models")

    click.echo(f"\n💡 Pro Tips:")
    click.echo("  • Use --regex-only for fastest processing")
    click.echo("  • Use --profile to apply pre-configured settings")
    click.echo("  • Use multiple pattern packs: --pattern-packs default --pattern-packs healthcare")
    click.echo("  • Use validate-config to check your custom configurations")
    click.echo("  • Start with 'minimal' profile if you're unsure")

    click.echo(f"\n📚 Full documentation: See docs/ directory or README.md")
    click.echo("🆘 Need help? Run any command with --help")


@cli.command(name="list-profiles")
def list_profiles() -> None:
    """List available configuration profiles."""
    try:
        from maskingengine.core import ConfigResolver

        # Read profiles file directly to get descriptions
        profiles_file = Path(__file__).parent.parent / "core" / "profiles.yaml"
        if not profiles_file.exists():
            click.echo("📭 No configuration profiles found")
            return

        with open(profiles_file, "r") as f:
            profiles_data = yaml.safe_load(f) or {}

        if not profiles_data:
            click.echo("📭 No profiles configured")
            return

        click.echo(f"📋 Found {len(profiles_data)} configuration profiles:")
        click.echo("\n💡 Quick Start: Try 'maskingengine getting-started' for a guided setup\n")

        # Define usage recommendations and performance info
        profile_recommendations = {
            "minimal": ("🚀 Best for: High-speed processing, structured data", "~10ms"),
            "standard": ("⚖️  Best for: General use, balanced speed/accuracy", "~200ms"),
            "healthcare-en": ("🏥 Best for: Medical records, HIPAA compliance", "~50ms"),
            "finance-en": ("💰 Best for: Financial data, credit cards, SSNs", "~200ms"),
            "high-security": ("🔒 Best for: Maximum detection, security-critical", "~300ms"),
        }

        for profile_name, profile_data in profiles_data.items():
            click.echo(f"• {profile_name}")
            description = profile_data.get("description", "No description")
            click.echo(f"  Description: {description}")

            # Add usage recommendation and performance
            if profile_name in profile_recommendations:
                recommendation, perf = profile_recommendations[profile_name]
                click.echo(f"  {recommendation}")
                click.echo(f"  Performance: {perf} typical processing time")

            regex_only = profile_data.get("regex_only", False)
            mode = "Regex-only" if regex_only else "Full pipeline (regex + NER)"
            click.echo(f"  Mode: {mode}")

            pattern_packs = profile_data.get("regex_packs", [])
            if pattern_packs:
                click.echo(f"  Pattern packs: {', '.join(pattern_packs)}")

            ner_models = profile_data.get("ner_models", [])
            if ner_models:
                click.echo(f"  NER models: {', '.join(ner_models)}")

            # Add usage example
            click.echo(
                f"  Usage: maskingengine mask input.txt --profile {profile_name} -o output.txt"
            )

            click.echo()

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
