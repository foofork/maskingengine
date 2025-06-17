"""Tests for the CLI interface."""

import pytest
import json
import tempfile
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from maskingengine.cli.main import cli


class TestCLICommands:
    """Test all CLI commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_cli_version(self):
        """Test CLI version display."""
        result = self.runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert "1.01.00" in result.output
        assert "maskingengine" in result.output
    
    def test_cli_help(self):
        """Test CLI help."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "MaskingEngine CLI" in result.output
        assert "mask" in result.output
        assert "test" in result.output
    
    def test_mask_command_stdin(self):
        """Test mask command with stdin input."""
        test_content = "Contact john@example.com or call 555-123-4567"
        result = self.runner.invoke(cli, ['mask', '--stdin', '--regex-only'], input=test_content)
        assert result.exit_code == 0
        # Should contain masked placeholders
        assert "<<EMAIL_" in result.output or "<<PHONE_" in result.output
        assert "Detected" in result.output
    
    def test_mask_command_with_file(self):
        """Test mask command with file input."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Email: test@example.com\nPhone: 555-1234")
            temp_file = f.name
        
        try:
            result = self.runner.invoke(cli, ['mask', temp_file, '--regex-only'])
            assert result.exit_code == 0
            assert "<<EMAIL_" in result.output or "<<PHONE_" in result.output
        finally:
            Path(temp_file).unlink()
    
    def test_mask_command_with_output_file(self):
        """Test mask command writing to output file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as input_f:
            input_f.write("Contact: admin@company.com")
            input_file = input_f.name
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as output_f:
            output_file = output_f.name
        
        try:
            result = self.runner.invoke(cli, [
                'mask', input_file, '-o', output_file, '--regex-only'
            ])
            assert result.exit_code == 0
            assert "Sanitized content written to" in result.output
            
            # Check output file contains masked content
            output_content = Path(output_file).read_text()
            assert "<<EMAIL_" in output_content
        finally:
            Path(input_file).unlink()
            Path(output_file).unlink()
    
    def test_mask_command_with_whitelist(self):
        """Test mask command with whitelist."""
        test_content = "Email support@company.com or personal@example.com"
        result = self.runner.invoke(cli, [
            'mask', '--stdin', '--regex-only',
            '--whitelist', 'support@company.com'
        ], input=test_content)
        assert result.exit_code == 0
        # support@company.com should not be masked
        output_lower = result.output.lower()
        assert "support@company.com" in output_lower
    
    def test_mask_command_with_pattern_packs(self):
        """Test mask command with custom pattern packs."""
        test_content = "Email: test@example.com"
        result = self.runner.invoke(cli, [
            'mask', '--stdin', '--regex-only',
            '--pattern-packs', 'default'
        ], input=test_content)
        assert result.exit_code == 0
        assert "<<EMAIL_" in result.output
    
    def test_test_command(self):
        """Test the test command."""
        result = self.runner.invoke(cli, ['test'])
        assert result.exit_code == 0
        assert "Testing MaskingEngine" in result.output
        assert "Test completed" in result.output
        assert "Detected" in result.output
    
    def test_test_command_with_session(self):
        """Test the test command with rehydration session."""
        result = self.runner.invoke(cli, ['test', '--session-id', 'test-session-cli'])
        assert result.exit_code == 0
        assert "Testing rehydration" in result.output
        assert "Rehydration test" in result.output
    
    def test_rehydrate_command(self):
        """Test rehydrate command."""
        # Create temporary masked file and mask map
        masked_content = "Contact <<EMAIL_ABC123_1>> for details"
        mask_map = {"<<EMAIL_ABC123_1>>": "admin@example.com"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as masked_f:
            masked_f.write(masked_content)
            masked_file = masked_f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as map_f:
            json.dump(mask_map, map_f)
            map_file = map_f.name
        
        try:
            result = self.runner.invoke(cli, ['rehydrate', masked_file, map_file])
            assert result.exit_code == 0
            assert "admin@example.com" in result.output
            assert "Processed 1 placeholders" in result.output
        finally:
            Path(masked_file).unlink()
            Path(map_file).unlink()
    
    def test_session_sanitize_command(self):
        """Test session-sanitize command."""
        # Create a temp file to avoid Click validation issues  
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Contact: sales@company.com")
            temp_file = f.name
            
        try:
            result = self.runner.invoke(cli, [
                'session-sanitize', temp_file, 'test-session-123',
                '--regex-only'
            ])
            assert result.exit_code == 0
            assert "Session 'test-session-123' created" in result.output
            assert "<<EMAIL_" in result.output
        finally:
            Path(temp_file).unlink()
    
    def test_session_rehydrate_command(self):
        """Test session-rehydrate command."""
        # First create a session using a temp file
        test_content = "Email: contact@example.com"
        session_id = "test-rehydrate-session"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file = f.name
        
        try:
            create_result = self.runner.invoke(cli, [
                'session-sanitize', temp_file, session_id, '--regex-only'
            ])
            assert create_result.exit_code == 0
        
            # Extract masked content from output
            lines = create_result.output.strip().split('\n')
            masked_content = None
            for line in lines:
                if "<<EMAIL_" in line:
                    masked_content = line.strip()
                    break
            
            assert masked_content is not None
            
            # Create a dummy file for rehydration (needed for Click argument parsing)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as dummy_f:
                dummy_f.write("dummy")
                dummy_file = dummy_f.name
            
            try:
                # Now rehydrate using file method instead of stdin to avoid Click parsing issues
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as masked_f:
                    masked_f.write(masked_content)
                    masked_file = masked_f.name
                
                try:
                    result = self.runner.invoke(cli, [
                        'session-rehydrate', masked_file, session_id
                    ])
                    assert result.exit_code == 0
                    assert "contact@example.com" in result.output
                finally:
                    Path(masked_file).unlink()
            finally:
                Path(dummy_file).unlink()
        finally:
            Path(temp_file).unlink()
    
    def test_sessions_command(self):
        """Test sessions listing command."""
        result = self.runner.invoke(cli, ['sessions'])
        assert result.exit_code == 0
        # Should either show sessions or "No active sessions"
        assert "sessions" in result.output.lower()
    
    def test_cleanup_sessions_command(self):
        """Test cleanup-sessions command."""
        result = self.runner.invoke(cli, ['cleanup-sessions', '--max-age-hours', '1'])
        assert result.exit_code == 0
        assert "Cleanup completed" in result.output
    
    def test_validate_config_command(self):
        """Test validate-config command."""
        result = self.runner.invoke(cli, ['validate-config', '--profile', 'minimal'])
        assert result.exit_code == 0
        assert "Configuration is valid" in result.output
    
    def test_validate_config_with_file(self):
        """Test validate-config with config file."""
        config_data = {
            "regex_only": True,
            "regex_packs": ["default"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            result = self.runner.invoke(cli, ['validate-config', config_file])
            assert result.exit_code == 0
            assert "Configuration is valid" in result.output
        finally:
            Path(config_file).unlink()
    
    def test_list_models_command(self):
        """Test list-models command."""
        result = self.runner.invoke(cli, ['list-models'])
        assert result.exit_code == 0
        # Should show registered models or "No models"
        assert "models" in result.output.lower()
    
    def test_list_packs_command(self):
        """Test list-packs command."""
        result = self.runner.invoke(cli, ['list-packs'])
        assert result.exit_code == 0
        assert "pattern packs" in result.output
        assert "default" in result.output  # Should have default pack
    
    def test_test_sample_command(self):
        """Test test-sample command."""
        result = self.runner.invoke(cli, [
            'test-sample', 'Contact john@example.com',
            '--regex-only'
        ])
        assert result.exit_code == 0
        assert "Original:" in result.output
        assert "Masked:" in result.output
        assert "john@example.com" in result.output
        assert "<<EMAIL_" in result.output
    
    def test_test_sample_with_profile(self):
        """Test test-sample with profile."""
        result = self.runner.invoke(cli, [
            'test-sample', 'Email: admin@company.com',
            '--profile', 'minimal'
        ])
        assert result.exit_code == 0
        assert "Masked:" in result.output
    
    def test_invalid_profile_handling(self):
        """Test handling of invalid profile."""
        result = self.runner.invoke(cli, [
            'validate-config', '--profile', 'nonexistent-profile'
        ])
        assert result.exit_code == 1  # Should exit with error
        assert "Configuration is invalid" in result.output
    
    def test_json_format_handling(self):
        """Test JSON format handling in mask command."""
        json_content = '{"name": "John Doe", "email": "john@example.com"}'
        result = self.runner.invoke(cli, [
            'mask', '--stdin', '--format', 'json', '--regex-only'
        ], input=json_content)
        assert result.exit_code == 0
        # Should handle JSON format
        assert "<<EMAIL_" in result.output
    
    def test_error_handling_missing_file(self):
        """Test error handling for missing input file."""
        result = self.runner.invoke(cli, ['mask', 'nonexistent-file.txt'])
        assert result.exit_code == 2  # Click parameter validation error
        assert "does not exist" in result.output
    
    def test_error_handling_invalid_json_mask_map(self):
        """Test error handling for invalid JSON mask map."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as masked_f:
            masked_f.write("test content")
            masked_file = masked_f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as map_f:
            map_f.write("invalid json content")
            map_file = map_f.name
        
        try:
            result = self.runner.invoke(cli, ['rehydrate', masked_file, map_file])
            assert result.exit_code == 1
            assert "Invalid JSON" in result.output
        finally:
            Path(masked_file).unlink()
            Path(map_file).unlink()