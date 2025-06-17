"""Tests for the REST API endpoints."""

import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from maskingengine.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestAPIEndpoints:
    """Test all API endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert data["service"] == "MaskingEngine API"
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "ner_enabled" in data
    
    def test_sanitize_endpoint(self, client):
        """Test sanitize endpoint."""
        payload = {
            "content": "Contact john@example.com or call 555-123-4567",
            "regex_only": True
        }
        response = client.post("/sanitize", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "sanitized_content" in data
        assert "mask_map" in data
        assert "detection_count" in data
        # Should have masked the email and phone
        assert data["sanitized_content"] != payload["content"]
        assert len(data["mask_map"]) > 0
    
    def test_sanitize_with_whitelist(self, client):
        """Test sanitize with whitelist."""
        payload = {
            "content": "Email support@company.com or personal@example.com",
            "whitelist": ["support@company.com"],
            "regex_only": True
        }
        response = client.post("/sanitize", json=payload)
        assert response.status_code == 200
        data = response.json()
        # support@company.com should not be masked, personal@example.com should be
        assert "support@company.com" in data["sanitized_content"]
        assert "personal@example.com" not in data["sanitized_content"]
    
    def test_rehydrate_endpoint(self, client):
        """Test rehydrate endpoint."""
        # First sanitize some content
        sanitize_payload = {
            "content": "Contact john@example.com",
            "regex_only": True
        }
        sanitize_response = client.post("/sanitize", json=sanitize_payload)
        sanitize_data = sanitize_response.json()
        
        # Then rehydrate it
        rehydrate_payload = {
            "masked_content": sanitize_data["sanitized_content"],
            "mask_map": sanitize_data["mask_map"]
        }
        response = client.post("/rehydrate", json=rehydrate_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["rehydrated_content"] == sanitize_payload["content"]
    
    def test_session_sanitize_endpoint(self, client):
        """Test session-based sanitization."""
        payload = {
            "content": "Contact jane@example.com",
            "session_id": "test-session-123",
            "regex_only": True
        }
        response = client.post("/session/sanitize", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "sanitized_content" in data
        assert "session_id" in data
        assert data["session_id"] == "test-session-123"
    
    def test_session_rehydrate_endpoint(self, client):
        """Test session-based rehydration."""
        # First create a session
        session_id = "test-session-456"
        sanitize_payload = {
            "content": "Email test@example.com",
            "session_id": session_id,
            "regex_only": True
        }
        sanitize_response = client.post("/session/sanitize", json=sanitize_payload)
        sanitize_data = sanitize_response.json()
        
        # Then rehydrate using session
        rehydrate_payload = {
            "masked_content": sanitize_data["sanitized_content"],
            "session_id": session_id
        }
        response = client.post("/session/rehydrate", json=rehydrate_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["rehydrated_content"] == sanitize_payload["content"]
    
    def test_sessions_list_endpoint(self, client):
        """Test listing sessions."""
        response = client.get("/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)
    
    def test_config_validate_endpoint(self, client):
        """Test config validation endpoint."""
        payload = {
            "config": {
                "regex_only": True,
                "regex_packs": ["default"]
            }
        }
        response = client.post("/config/validate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "explanation" in data
        assert data["status"] in ["valid", "invalid"]
    
    def test_config_validate_with_profile(self, client):
        """Test config validation with profile."""
        payload = {
            "profile": "minimal"
        }
        response = client.post("/config/validate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "valid"
        assert "minimal" in data["explanation"].lower()
    
    def test_discover_endpoint(self, client):
        """Test discovery endpoint."""
        response = client.get("/discover")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "pattern_packs" in data
        assert "profiles" in data
        assert isinstance(data["models"], list)
        assert isinstance(data["pattern_packs"], list)
        assert isinstance(data["profiles"], list)
    
    def test_models_endpoint(self, client):
        """Test models listing endpoint."""
        response = client.get("/models")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least the distilbert model from models.yaml
        if data:  # If models.yaml exists and has models
            model = data[0]
            assert "id" in model
            assert "name" in model
            assert "type" in model
    
    def test_pattern_packs_endpoint(self, client):
        """Test pattern packs listing endpoint."""
        response = client.get("/pattern-packs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least the default pattern pack
        pack_names = [pack["name"] for pack in data]
        assert "default" in pack_names
    
    def test_profiles_endpoint(self, client):
        """Test profiles listing endpoint."""
        response = client.get("/profiles")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have the predefined profiles
        profile_names = [profile["name"] for profile in data]
        assert "minimal" in profile_names
        assert "healthcare-en" in profile_names
    
    def test_invalid_json_handling(self, client):
        """Test handling of invalid JSON content."""
        payload = {
            "content": '{"invalid": json content}',
            "format": "json"
        }
        response = client.post("/sanitize", json=payload)
        # Should handle gracefully and treat as text
        assert response.status_code == 200
    
    def test_session_cleanup(self, client):
        """Test session cleanup."""
        session_id = "cleanup-test-session"
        
        # Create a session
        sanitize_payload = {
            "content": "Test content",
            "session_id": session_id,
            "regex_only": True
        }
        client.post("/session/sanitize", json=sanitize_payload)
        
        # Delete the session
        response = client.delete(f"/session/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["message"].lower()
    
    def test_error_handling(self, client):
        """Test API error handling."""
        # Test with invalid profile
        payload = {
            "profile": "nonexistent-profile"
        }
        response = client.post("/config/validate", json=payload)
        assert response.status_code == 200  # Should return validation error, not HTTP error
        data = response.json()
        assert data["status"] == "invalid"
        
        # Test rehydration with invalid session
        rehydrate_payload = {
            "masked_content": "test content",
            "session_id": "nonexistent-session"
        }
        response = client.post("/session/rehydrate", json=rehydrate_payload)
        assert response.status_code == 404  # Session not found