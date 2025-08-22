"""
Tests for the error handling middleware.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from middleware.error_handling import ErrorHandler, DatabaseErrorHandler, ValidationErrorHandler


class TestErrorHandler:
    """Test the ErrorHandler class."""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        request = Mock(spec=Request)
        request.url = "http://localhost:8000/api/claims/"
        request.method = "POST"
        request.headers = {"X-API-Key": "test-key"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        return request
    
    def test_handle_validation_error(self, mock_request):
        """Test handling Pydantic validation errors."""
        # Create a mock validation error
        validation_error = ValidationError.from_exception(
            ValueError("Invalid data")
        )
        validation_error.errors = [
            {
                "loc": ("field_name",),
                "msg": "Field is required",
                "type": "missing"
            }
        ]
        
        response = ErrorHandler.handle_validation_error(validation_error, mock_request)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422
        assert "validation_error" in response.body.decode()
        assert "Field is required" in response.body.decode()
    
    def test_handle_database_error_integrity_error(self, mock_request):
        """Test handling database integrity errors."""
        integrity_error = IntegrityError("Integrity constraint violated", None, None)
        
        response = ErrorHandler.handle_database_error(integrity_error, mock_request)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 409
        assert "Data integrity constraint violated" in response.body.decode()
    
    def test_handle_database_error_operational_error(self, mock_request):
        """Test handling database operational errors."""
        operational_error = OperationalError("Connection failed", None, None)
        
        response = ErrorHandler.handle_database_error(operational_error, mock_request)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 503
        assert "Database operation failed" in response.body.decode()
    
    def test_handle_database_error_generic(self, mock_request):
        """Test handling generic database errors."""
        generic_error = SQLAlchemyError("Unknown database error")
        
        response = ErrorHandler.handle_database_error(generic_error, mock_request)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        assert "Database error occurred" in response.body.decode()
    
    def test_handle_generic_error(self, mock_request):
        """Test handling generic exceptions."""
        generic_error = Exception("Something went wrong")
        
        response = ErrorHandler.handle_generic_error(generic_error, mock_request)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        assert "Internal server error" in response.body.decode()
    
    def test_handle_xml_validation_error(self, mock_request):
        """Test handling XML validation errors."""
        validation_errors = ["Invalid XML structure", "Missing required element"]
        
        response = ErrorHandler.handle_xml_validation_error(validation_errors, mock_request)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422
        assert "XML validation failed" in response.body.decode()
        assert "Invalid XML structure" in response.body.decode()
    
    def test_handle_rate_limit_error(self, mock_request):
        """Test handling rate limit errors."""
        retry_after = 60
        
        response = ErrorHandler.handle_rate_limit_error(retry_after, mock_request)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.body.decode()
        assert "60" in response.body.decode()
    
    def test_handle_authentication_error(self, mock_request):
        """Test handling authentication errors."""
        error_detail = "Invalid API key"
        
        response = ErrorHandler.handle_authentication_error(error_detail, mock_request)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
        assert "Authentication failed" in response.body.decode()
        assert "Invalid API key" in response.body.decode()


class TestDatabaseErrorHandler:
    """Test the DatabaseErrorHandler class."""
    
    def test_safe_database_operation_success(self):
        """Test successful database operation."""
        def successful_operation():
            return "success"
        
        result = DatabaseErrorHandler.safe_database_operation(successful_operation)
        assert result == "success"
    
    def test_safe_database_operation_integrity_error(self):
        """Test database operation with integrity error."""
        def failing_operation():
            raise IntegrityError("Constraint violated", None, None)
        
        with pytest.raises(HTTPException) as exc_info:
            DatabaseErrorHandler.safe_database_operation(failing_operation)
        
        assert exc_info.value.status_code == 409
        assert "Data integrity constraint violated" in str(exc_info.value.detail)
    
    def test_safe_database_operation_operational_error(self):
        """Test database operation with operational error."""
        def failing_operation():
            raise OperationalError("Connection failed", None, None)
        
        with pytest.raises(HTTPException) as exc_info:
            DatabaseErrorHandler.safe_database_operation(failing_operation)
        
        assert exc_info.value.status_code == 503
        assert "Database operation failed" in str(exc_info.value.detail)
    
    def test_safe_database_operation_generic_error(self):
        """Test database operation with generic error."""
        def failing_operation():
            raise SQLAlchemyError("Unknown error")
        
        with pytest.raises(HTTPException) as exc_info:
            DatabaseErrorHandler.safe_database_operation(failing_operation)
        
        assert exc_info.value.status_code == 500
        assert "Database error occurred" in str(exc_info.value.detail)


class TestValidationErrorHandler:
    """Test the ValidationErrorHandler class."""
    
    def test_validate_required_fields_success(self):
        """Test successful required field validation."""
        data = {"name": "John", "email": "john@example.com"}
        required_fields = ["name", "email"]
        
        result = ValidationErrorHandler.validate_required_fields(data, required_fields)
        assert result is True
    
    def test_validate_required_fields_missing(self):
        """Test required field validation with missing fields."""
        data = {"name": "John"}
        required_fields = ["name", "email"]
        
        with pytest.raises(ValueError, match="Missing required fields: email"):
            ValidationErrorHandler.validate_required_fields(data, required_fields)
    
    def test_validate_field_types_success(self):
        """Test successful field type validation."""
        data = {"age": 25, "name": "John"}
        field_types = {"age": int, "name": str}
        
        result = ValidationErrorHandler.validate_field_types(data, field_types)
        assert result is True
    
    def test_validate_field_types_mismatch(self):
        """Test field type validation with type mismatch."""
        data = {"age": "25", "name": "John"}
        field_types = {"age": int, "name": str}
        
        with pytest.raises(ValueError, match="Field 'age' must be of type <class 'int'>, got <class 'str'>"):
            ValidationErrorHandler.validate_field_types(data, field_types)
    
    def test_validate_field_values_success(self):
        """Test successful field value validation."""
        data = {"status": "active", "priority": "high"}
        field_values = {
            "status": ["active", "inactive"],
            "priority": ["low", "medium", "high"]
        }
        
        result = ValidationErrorHandler.validate_field_values(data, field_values)
        assert result is True
    
    def test_validate_field_values_invalid(self):
        """Test field value validation with invalid values."""
        data = {"status": "invalid", "priority": "high"}
        field_values = {
            "status": ["active", "inactive"],
            "priority": ["low", "medium", "high"]
        }
        
        with pytest.raises(ValueError, match="Field 'status' must be one of: active, inactive"):
            ValidationErrorHandler.validate_field_values(data, field_values)


class TestErrorHandlerIntegration:
    """Test error handler integration scenarios."""
    
    def test_error_handler_initialization(self):
        """Test that ErrorHandler can be used statically."""
        # All methods should be static and accessible
        assert hasattr(ErrorHandler, 'handle_validation_error')
        assert hasattr(ErrorHandler, 'handle_database_error')
        assert hasattr(ErrorHandler, 'handle_generic_error')
        assert hasattr(ErrorHandler, 'handle_xml_validation_error')
        assert hasattr(ErrorHandler, 'handle_rate_limit_error')
        assert hasattr(ErrorHandler, 'handle_authentication_error')
    
    def test_database_error_handler_initialization(self):
        """Test that DatabaseErrorHandler can be used statically."""
        assert hasattr(DatabaseErrorHandler, 'safe_database_operation')
    
    def test_validation_error_handler_initialization(self):
        """Test that ValidationErrorHandler can be used statically."""
        assert hasattr(ValidationErrorHandler, 'validate_required_fields')
        assert hasattr(ValidationErrorHandler, 'validate_field_types')
        assert hasattr(ValidationErrorHandler, 'validate_field_values')
    
    def test_error_response_structure(self):
        """Test that error responses have consistent structure."""
        mock_request = Mock()
        mock_request.url = "http://localhost:8000/api/test"
        mock_request.method = "GET"
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        
        # Test validation error response structure
        validation_error = ValidationError.from_exception(ValueError("Test"))
        validation_error.errors = [{"loc": ("test",), "msg": "Test error", "type": "test"}]
        
        response = ErrorHandler.handle_validation_error(validation_error, mock_request)
        response_data = response.body.decode()
        
        # Check response structure
        assert "error_type" in response_data
        assert "message" in response_data
        assert "details" in response_data
        assert "timestamp" in response_data
        assert "request_id" in response_data


if __name__ == "__main__":
    pytest.main([__file__]) 