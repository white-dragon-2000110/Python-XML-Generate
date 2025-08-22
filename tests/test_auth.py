"""
Tests for the authentication middleware.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from middleware.auth import APIKeyAuth, get_current_user, require_auth, get_auth_headers


class TestAPIKeyAuth:
    """Test the APIKeyAuth class."""
    
    def test_init_with_default_values(self):
        """Test initialization with default values."""
        auth = APIKeyAuth()
        assert auth.api_key_header == "X-API-Key"
        assert auth.rate_limit_requests == 100
        assert auth.rate_limit_window == 3600
    
    def test_init_with_default_values(self):
        """Test initialization with default values."""
        auth = APIKeyAuth()
        assert auth.api_key_header == "X-API-Key"
        assert auth.rate_limit_requests == 100
        assert auth.rate_limit_window == 3600
    
    def test_validate_api_key_valid(self):
        """Test API key validation with valid key."""
        auth = APIKeyAuth()
        # Set environment variable for testing
        import os
        os.environ["API_KEY"] = "test-key-123"
        auth.valid_api_keys = {"test-key-123", "key2", "key3"}
        
        assert auth.validate_api_key("test-key-123") is True
        assert auth.validate_api_key("key2") is True
        assert auth.validate_api_key("key3") is True
    
    def test_validate_api_key_invalid(self):
        """Test API key validation with invalid key."""
        auth = APIKeyAuth()
        auth.api_keys = ["key1", "key2", "key3"]
        
        assert auth.validate_api_key("invalid") is False
        assert auth.validate_api_key("") is False
        assert auth.validate_api_key(None) is False
    
    def test_get_client_ip_from_x_forwarded_for(self):
        """Test getting client IP from X-Forwarded-For header."""
        auth = APIKeyAuth()
        request = Mock()
        request.headers = {"X-Forwarded-For": "192.168.1.100, 10.0.0.1"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        ip = auth.get_client_ip(request)
        assert ip == "192.168.1.100"
    
    def test_get_client_ip_from_x_real_ip(self):
        """Test getting client IP from X-Real-IP header."""
        auth = APIKeyAuth()
        request = Mock()
        request.headers = {"X-Real-IP": "192.168.1.200"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        ip = auth.get_client_ip(request)
        assert ip == "192.168.1.200"
    
    def test_get_client_ip_from_client_host(self):
        """Test getting client IP from client.host."""
        auth = APIKeyAuth()
        request = Mock()
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.300"
        
        ip = auth.get_client_ip(request)
        assert ip == "192.168.1.300"
    
    def test_check_rate_limit_new_client(self):
        """Test rate limiting for new client."""
        auth = APIKeyAuth()
        client_ip = "192.168.1.100"
        api_key = "test-key"
        
        # First request should pass
        assert auth.check_rate_limit(client_ip, api_key) is True
        
        # Check that client is tracked
        key = f"{client_ip}:{api_key}"
        assert key in auth.rate_limit_data
        # Rate limit data is stored as (timestamp, count) tuple
        assert auth.rate_limit_data[key][1] == 1
    
    def test_check_rate_limit_existing_client(self):
        """Test rate limiting for existing client."""
        auth = APIKeyAuth()
        auth.rate_limit_requests = 2
        client_ip = "192.168.1.100"
        api_key = "test-key"
        
        # First two requests should pass
        assert auth.check_rate_limit(client_ip, api_key) is True
        assert auth.check_rate_limit(client_ip, api_key) is True
        
        # Third request should be blocked
        assert auth.check_rate_limit(client_ip, api_key) is False
    
    def test_check_rate_limit_window_reset(self):
        """Test rate limit window reset."""
        auth = APIKeyAuth()
        auth.rate_limit_requests = 1
        auth.rate_limit_window = 1  # 1 second window
        client_ip = "192.168.1.100"
        api_key = "test-key"
        
        # First request should pass
        assert auth.check_rate_limit(client_ip, api_key) is True
        
        # Second request should be blocked
        assert auth.check_rate_limit(client_ip, api_key) is False
        
        # Wait for window to reset
        import time
        time.sleep(1.1)
        
        # Request should pass again
        assert auth.check_rate_limit(client_ip, api_key) is True


class TestAuthentication:
    """Test the authentication functions."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test successful authentication."""
        request = Mock()
        request.headers = {"X-API-Key": "test-key"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Mock the global auth_middleware
        with patch('middleware.auth.auth_middleware') as mock_auth:
            mock_auth.authenticate = AsyncMock(return_value={
                "authenticated": True,
                "api_key": "test-key",
                "client_ip": "192.168.1.100"
            })
            
            result = await get_current_user(request)
            
            assert result["authenticated"] is True
            assert result["api_key"] == "test-key"
            assert result["client_ip"] == "192.168.1.100"
    
    @pytest.mark.asyncio
    async def test_get_current_user_failure(self):
        """Test authentication failure."""
        request = Mock()
        request.headers = {"X-API-Key": "invalid-key"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Mock the global auth_middleware to raise an exception
        with patch('middleware.auth.auth_middleware') as mock_auth:
            mock_auth.authenticate.side_effect = HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(request)
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid API key"
    
    @pytest.mark.asyncio
    async def test_require_auth_dependency(self):
        """Test the require_auth dependency function."""
        # This is a simple wrapper, so we just test it returns the function
        assert callable(require_auth)
        
        # Test that it can be used as a dependency
        request = Mock()
        request.headers = {"X-API-Key": "test-key"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Mock the global auth_middleware
        with patch('middleware.auth.auth_middleware') as mock_auth:
            mock_auth.authenticate = AsyncMock(return_value={
                "authenticated": True,
                "api_key": "test-key",
                "client_ip": "127.0.0.1"
            })
            
            result = await require_auth(request)
            assert isinstance(result, dict)
            assert result["authenticated"] is True


class TestRateLimitHeaders:
    """Test rate limit header generation."""
    
    def test_get_auth_headers(self):
        """Test getting authentication headers."""
        request = Mock()
        request.headers = {"X-API-Key": "test-key"}
        request.client = Mock()
        request.client.host = "192.168.1.100"
        
        # Test the global function
        headers = get_auth_headers(request)
        
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Window" in headers


if __name__ == "__main__":
    pytest.main([__file__]) 