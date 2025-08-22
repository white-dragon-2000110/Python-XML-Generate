from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from pydantic import ValidationError
from typing import Union, Dict, Any
import traceback
import logging
from datetime import datetime

logger = logging.getLogger("tiss_api")

class ErrorHandler:
    """Centralized error handling for the API"""
    
    @staticmethod
    def handle_validation_error(error: ValidationError, request: Request) -> JSONResponse:
        """
        Handle Pydantic validation errors
        
        Args:
            error: ValidationError from Pydantic
            request: FastAPI request object
            
        Returns:
            JSONResponse: Formatted error response
        """
        error_details = []
        for error_item in error.errors():
            error_details.append({
                "field": " -> ".join(str(loc) for loc in error_item["loc"]),
                "message": error_item["msg"],
                "type": error_item["type"]
            })
        
        error_response = {
            "error": "Validation Error",
            "message": "Invalid data provided",
            "details": error_details,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url),
            "method": request.method
        }
        
        logger.warning(f"Validation error: {error_details}")
        return JSONResponse(status_code=422, content=error_response)
    
    @staticmethod
    def handle_database_error(error: SQLAlchemyError, request: Request) -> JSONResponse:
        """
        Handle database-related errors
        
        Args:
            error: SQLAlchemy error
            request: FastAPI request object
            
        Returns:
            JSONResponse: Formatted error response
        """
        error_type = type(error).__name__
        
        if isinstance(error, IntegrityError):
            # Handle constraint violations
            error_message = "Data integrity constraint violated"
            status_code = 409  # Conflict
            error_details = str(error.orig) if hasattr(error, 'orig') else str(error)
            
        elif isinstance(error, OperationalError):
            # Handle connection/operational errors
            error_message = "Database operation failed"
            status_code = 503  # Service Unavailable
            error_details = "Database connection or operation error"
            
        else:
            # Handle other database errors
            error_message = "Database error occurred"
            status_code = 500  # Internal Server Error
            error_details = str(error)
        
        error_response = {
            "error": "Database Error",
            "message": error_message,
            "type": error_type,
            "details": error_details,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url),
            "method": request.method
        }
        
        logger.error(f"Database error ({error_type}): {error_details}")
        return JSONResponse(status_code=status_code, content=error_response)
    
    @staticmethod
    def handle_generic_error(error: Exception, request: Request) -> JSONResponse:
        """
        Handle generic exceptions
        
        Args:
            error: Generic exception
            request: FastAPI request object
            
        Returns:
            JSONResponse: Formatted error response
        """
        error_response = {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "type": type(error).__name__,
            "details": str(error),
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url),
            "method": request.method
        }
        
        # Log the full error with traceback
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        return JSONResponse(status_code=500, content=error_response)
    
    @staticmethod
    def handle_xml_validation_error(error: Exception, request: Request, xml_content: str = None) -> JSONResponse:
        """
        Handle XML validation errors
        
        Args:
            error: XML validation error
            request: FastAPI request object
            xml_content: XML content that failed validation
            
        Returns:
            JSONResponse: Formatted error response
        """
        error_response = {
            "error": "XML Validation Error",
            "message": "XML content failed validation",
            "type": type(error).__name__,
            "details": str(error),
            "xml_size": len(xml_content) if xml_content else 0,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url),
            "method": request.method
        }
        
        logger.error(f"XML validation error: {str(error)}")
        return JSONResponse(status_code=422, content=error_response)
    
    @staticmethod
    def handle_rate_limit_error(request: Request, retry_after: int = None) -> JSONResponse:
        """
        Handle rate limiting errors
        
        Args:
            request: FastAPI request object
            retry_after: Seconds to wait before retrying
            
        Returns:
            JSONResponse: Formatted error response
        """
        error_response = {
            "error": "Rate Limit Exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": retry_after,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url),
            "method": request.method
        }
        
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        
        logger.warning(f"Rate limit exceeded for {request.client.host}")
        return JSONResponse(status_code=429, content=error_response, headers=headers)
    
    @staticmethod
    def handle_authentication_error(request: Request, details: str = None) -> JSONResponse:
        """
        Handle authentication errors
        
        Args:
            request: FastAPI request object
            details: Additional error details
            
        Returns:
            JSONResponse: Formatted error response
        """
        error_response = {
            "error": "Authentication Failed",
            "message": "Invalid or missing API key",
            "details": details or "Please provide a valid API key in the X-API-Key header",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url),
            "method": request.method
        }
        
        logger.warning(f"Authentication failed for {request.client.host}")
        return JSONResponse(
            status_code=401, 
            content=error_response,
            headers={"WWW-Authenticate": "X-API-Key"}
        )

class DatabaseErrorHandler:
    """Specialized handler for database operations"""
    
    @staticmethod
    def safe_database_operation(operation_func, *args, **kwargs):
        """
        Safely execute database operations with error handling
        
        Args:
            operation_func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result of the operation
            
        Raises:
            HTTPException: If database operation fails
        """
        try:
            return operation_func(*args, **kwargs)
        except IntegrityError as e:
            logger.error(f"Database integrity error: {str(e)}")
            raise HTTPException(
                status_code=409,
                detail="Data integrity constraint violated. Please check your data."
            )
        except OperationalError as e:
            logger.error(f"Database operational error: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail="Database service temporarily unavailable. Please try again later."
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Database error occurred. Please try again later."
            )
        except Exception as e:
            logger.error(f"Unexpected error in database operation: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred. Please try again later."
            )

class ValidationErrorHandler:
    """Specialized handler for data validation"""
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
        """
        Validate that required fields are present
        
        Args:
            data: Data dictionary to validate
            required_fields: List of required field names
            
        Raises:
            HTTPException: If required fields are missing
        """
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
    
    @staticmethod
    def validate_field_types(data: Dict[str, Any], field_types: Dict[str, type]) -> None:
        """
        Validate field types
        
        Args:
            data: Data dictionary to validate
            field_types: Dictionary mapping field names to expected types
            
        Raises:
            HTTPException: If field types are incorrect
        """
        for field, expected_type in field_types.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Field '{field}' must be of type {expected_type.__name__}"
                    )
    
    @staticmethod
    def validate_field_values(data: Dict[str, Any], field_validators: Dict[str, callable]) -> None:
        """
        Validate field values using custom validators
        
        Args:
            data: Data dictionary to validate
            field_validators: Dictionary mapping field names to validation functions
            
        Raises:
            HTTPException: If field validation fails
        """
        for field, validator in field_validators.items():
            if field in data and data[field] is not None:
                try:
                    validator(data[field])
                except ValueError as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Field '{field}' validation failed: {str(e)}"
                    )

# Global error handler instance
error_handler = ErrorHandler()
database_error_handler = DatabaseErrorHandler()
validation_error_handler = ValidationErrorHandler() 