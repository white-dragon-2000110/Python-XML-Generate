"""
Tests for the logging middleware.
"""

import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from middleware.logging import LoggingMiddleware, RequestLogger


class TestRequestLogger:
    """Test the RequestLogger utility class."""
    
    def test_log_database_operation(self):
        """Test database operation logging."""
        logger = RequestLogger()
        
        # Test successful operation
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            logger.log_database_operation("create", "claims", record_id=1, success=True, duration=0.5)
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "create" in call_args
            assert "claims" in call_args
            assert "1" in call_args
            assert "0.5" in call_args
    
    def test_log_xml_operation(self):
        """Test XML operation logging."""
        logger = RequestLogger()
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            logger.log_xml_operation("generation_start", claim_id=1, success=True, duration=0.3)
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "generation_start" in call_args
            assert "1" in call_args
            assert "0.3" in call_args
    
    def test_log_validation_operation(self):
        """Test validation operation logging."""
        logger = RequestLogger()
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            logger.log_validation_operation("xml_validation_start", content_length=1000, success=True, duration=0.2)
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "xml_validation_start" in call_args
            assert "1000" in call_args
            assert "0.2" in call_args
    
    def test_log_with_error(self):
        """Test logging with error information."""
        logger = RequestLogger()
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            logger.log_database_operation("create", "claims", success=False, error="Database connection failed")
            
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "create" in call_args
            assert "claims" in call_args
            assert "Database connection failed" in call_args


class TestLoggingMiddleware:
    """Test the LoggingMiddleware class."""
    
    @pytest.fixture
    def middleware(self):
        """Create a LoggingMiddleware instance."""
        return LoggingMiddleware()
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = "http://localhost:8000/api/claims/1"
        request.headers = {"User-Agent": "test-agent", "X-API-Key": "test-key"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.body = Mock()
        request.body.return_value = b"{}"
        return request
    
    @pytest.fixture
    def mock_response(self):
        """Create a mock response object."""
        response = Mock(spec=Response)
        response.status_code = 200
        response.headers = {"Content-Type": "application/json"}
        response.body = b'{"status": "success"}'
        return response
    
    @pytest.fixture
    def mock_call_next(self):
        """Create a mock call_next function."""
        async def call_next(request):
            response = Mock(spec=Response)
            response.status_code = 200
            response.headers = {"Content-Type": "application/json"}
            response.body = b'{"status": "success"}'
            return response
        return call_next
    
    @pytest.mark.asyncio
    async def test_dispatch_success(self, middleware, mock_request, mock_call_next):
        """Test successful middleware dispatch."""
        with patch('middleware.logging.time') as mock_time:
            mock_time.time.side_effect = [1000.0, 1000.5]  # start_time, end_time
            
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Check that response headers were added
            assert hasattr(response, 'headers')
            assert 'X-Request-ID' in response.headers
            assert 'X-Process-Time' in response.headers
            assert response.headers['X-Process-Time'] == '0.5'
    
    @pytest.mark.asyncio
    async def test_dispatch_with_error(self, middleware, mock_request):
        """Test middleware dispatch with error."""
        async def failing_call_next(request):
            raise Exception("Test error")
        
        with patch('middleware.logging.time') as mock_time:
            mock_time.time.side_effect = [1000.0, 1000.1]
            
            with pytest.raises(Exception, match="Test error"):
                await middleware.dispatch(mock_request, failing_call_next)
    
    @pytest.mark.asyncio
    async def test_log_request(self, middleware, mock_request):
        """Test request logging."""
        with patch('middleware.logging.logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            await middleware._log_request(mock_request, "test-request-id")
            
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args[0][0]
            assert "test-request-id" in call_args
            assert "GET" in call_args
            assert "/api/claims/1" in call_args
    
    @pytest.mark.asyncio
    async def test_log_response(self, middleware, mock_response):
        """Test response logging."""
        with patch('middleware.logging.logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            await middleware._log_response(mock_response, "test-request-id", 0.5)
            
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args[0][0]
            assert "test-request-id" in call_args
            assert "200" in call_args
            assert "0.5" in call_args
    
    @pytest.mark.asyncio
    async def test_log_error(self, middleware, mock_request):
        """Test error logging."""
        test_error = Exception("Test error message")
        
        with patch('middleware.logging.logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            await middleware._log_error(mock_request, "test-request-id", test_error, 0.1)
            
            mock_logger.error.assert_called()
            call_args = mock_logger.error.call_args[0][0]
            assert "test-request-id" in call_args
            assert "Test error message" in call_args
            assert "0.1" in call_args
    
    def test_get_request_body_text(self, middleware, mock_request):
        """Test getting request body as text."""
        # Test with JSON body
        mock_request.body.return_value = b'{"key": "value"}'
        body_text = middleware._get_request_body_text(mock_request)
        assert body_text == '{"key": "value"}'
        
        # Test with empty body
        mock_request.body.return_value = b''
        body_text = middleware._get_request_body_text(mock_request)
        assert body_text == ''
        
        # Test with binary body
        mock_request.body.return_value = b'\x00\x01\x02'
        body_text = middleware._get_request_body_text(mock_request)
        assert body_text == '<binary data>'
    
    def test_get_response_body_text(self, middleware, mock_response):
        """Test getting response body as text."""
        # Test with JSON body
        mock_response.body = b'{"status": "success"}'
        body_text = middleware._get_response_body_text(mock_response)
        assert body_text == '{"status": "success"}'
        
        # Test with empty body
        mock_response.body = b''
        body_text = middleware._get_response_body_text(mock_response)
        assert body_text == ''
        
        # Test with binary body
        mock_response.body = b'\x00\x01\x02'
        body_text = middleware._get_response_body_text(mock_response)
        assert body_text == '<binary data>'
    
    def test_truncate_body(self, middleware):
        """Test body truncation."""
        long_text = "x" * 1000
        truncated = middleware._truncate_body(long_text, max_length=500)
        assert len(truncated) == 500
        assert truncated.endswith("...")
        
        short_text = "short"
        truncated = middleware._truncate_body(short_text, max_length=500)
        assert truncated == short_text


class TestLoggingIntegration:
    """Test logging integration scenarios."""
    
    def test_logger_initialization(self):
        """Test that RequestLogger can be initialized."""
        logger = RequestLogger()
        assert logger is not None
        assert hasattr(logger, 'log_database_operation')
        assert hasattr(logger, 'log_xml_operation')
        assert hasattr(logger, 'log_validation_operation')
    
    def test_middleware_initialization(self):
        """Test that LoggingMiddleware can be initialized."""
        middleware = LoggingMiddleware()
        assert middleware is not None
        assert hasattr(middleware, 'dispatch')
        assert hasattr(middleware, '_log_request')
        assert hasattr(middleware, '_log_response')
        assert hasattr(middleware, '_log_error')
    
    @pytest.mark.asyncio
    async def test_full_request_cycle(self):
        """Test a complete request cycle through the middleware."""
        middleware = LoggingMiddleware()
        
        # Create mock request
        request = Mock(spec=Request)
        request.method = "POST"
        request.url = "http://localhost:8000/api/claims/"
        request.headers = {"Content-Type": "application/json"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.body = Mock()
        request.body.return_value = b'{"patient_id": 1}'
        
        # Create mock response
        response = Mock(spec=Response)
        response.status_code = 201
        response.headers = {"Content-Type": "application/json"}
        response.body = b'{"id": 1, "patient_id": 1}'
        
        # Mock call_next
        async def call_next(req):
            return response
        
        with patch('middleware.logging.time') as mock_time:
            mock_time.time.side_effect = [1000.0, 1000.3]
            
            result = await middleware.dispatch(request, call_next)
            
            # Verify response was returned
            assert result == response
            
            # Verify headers were added
            assert hasattr(result, 'headers')
            assert 'X-Request-ID' in result.headers
            assert 'X-Process-Time' in result.headers


if __name__ == "__main__":
    pytest.main([__file__]) 