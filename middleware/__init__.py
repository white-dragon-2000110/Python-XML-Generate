# Middleware package for TISS Healthcare API

from .auth import (
    APIKeyAuth,
    auth_middleware,
    get_current_user,
    require_auth,
    get_auth_headers
)

from .logging import (
    LoggingMiddleware,
    RequestLogger,
    request_logger
)

from .error_handling import (
    ErrorHandler,
    DatabaseErrorHandler,
    ValidationErrorHandler,
    error_handler,
    database_error_handler,
    validation_error_handler
)

__all__ = [
    # Authentication
    "APIKeyAuth",
    "auth_middleware",
    "get_current_user",
    "require_auth",
    "get_auth_headers",
    
    # Logging
    "LoggingMiddleware",
    "RequestLogger",
    "request_logger",
    
    # Error Handling
    "ErrorHandler",
    "DatabaseErrorHandler",
    "ValidationErrorHandler",
    "error_handler",
    "database_error_handler",
    "validation_error_handler"
] 