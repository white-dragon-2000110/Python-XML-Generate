import logging
import time
import json
from typing import Callable, Dict, Any
from fastapi import Request, Response
try:
    from fastapi.middleware.base import BaseHTTPMiddleware
except ImportError:
    # Fallback for older FastAPI versions
    from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
import uuid
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses"""
    
    def __init__(self, logger_name: str = "tiss_api"):
        self.logger = logging.getLogger(logger_name)
        
        # Configure log file if specified
        log_file = os.getenv("LOG_FILE")
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(file_handler)
        
        # Set log level from environment
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.logger.setLevel(getattr(logging, log_level))
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process the request and log details"""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Start timing
        start_time = time.time()
        
        # Log request
        await self._log_request(request, request_id)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            await self._log_response(response, request_id, process_time)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            await self._log_error(request, request_id, e, process_time)
            raise
    
    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request details"""
        # Extract request information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "Unknown")
        method = request.method
        url = str(request.url)
        
        # Get request body if it's a POST/PUT request
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Try to parse as JSON for logging
                    try:
                        body_json = json.loads(body.decode())
                        body = body_json
                    except:
                        body = body.decode()[:500] + "..." if len(body) > 500 else body.decode()
            except Exception:
                body = "Unable to read request body"
        
        # Create log entry
        log_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "type": "request",
            "method": method,
            "url": url,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "headers": dict(request.headers),
            "query_params": dict(request.query_params),
            "body": body
        }
        
        # Log at appropriate level
        if method in ["GET", "HEAD"]:
            self.logger.info(f"Request: {method} {url} from {client_ip}", extra={"log_data": log_data})
        else:
            self.logger.info(f"Request: {method} {url} from {client_ip}", extra={"log_data": log_data})
    
    async def _log_response(self, response: Response, request_id: str, process_time: float):
        """Log response details"""
        # Extract response information
        status_code = response.status_code
        headers = dict(response.headers)
        
        # Get response body if possible
        body = None
        if hasattr(response, 'body'):
            try:
                body = response.body.decode() if isinstance(response.body, bytes) else str(response.body)
                # Truncate long responses
                if len(body) > 1000:
                    body = body[:1000] + "..."
            except Exception:
                body = "Unable to read response body"
        
        # Create log entry
        log_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "type": "response",
            "status_code": status_code,
            "process_time": process_time,
            "headers": headers,
            "body": body
        }
        
        # Log at appropriate level based on status code
        if status_code < 400:
            self.logger.info(
                f"Response: {status_code} in {process_time:.3f}s", 
                extra={"log_data": log_data}
            )
        elif status_code < 500:
            self.logger.warning(
                f"Response: {status_code} in {process_time:.3f}s", 
                extra={"log_data": log_data}
            )
        else:
            self.logger.error(
                f"Response: {status_code} in {process_time:.3f}s", 
                extra={"log_data": log_data}
            )
    
    async def _log_error(self, request: Request, request_id: str, error: Exception, process_time: float):
        """Log error details"""
        # Extract request information
        client_ip = self._get_client_ip(request)
        method = request.method
        url = str(request.url)
        
        # Create log entry
        log_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "method": method,
            "url": url,
            "client_ip": client_ip,
            "process_time": process_time,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_details": {
                "args": error.args,
                "traceback": self._get_traceback(error)
            }
        }
        
        self.logger.error(
            f"Error processing {method} {url}: {type(error).__name__}: {str(error)}", 
            extra={"log_data": log_data}
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers (when behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        return request.client.host if request.client else "unknown"
    
    def _get_traceback(self, error: Exception) -> str:
        """Get traceback information for error"""
        import traceback
        try:
            return "".join(traceback.format_exception(type(error), error, error.__traceback__))
        except Exception:
            return "Unable to get traceback"

class RequestLogger:
    """Utility class for logging specific events"""
    
    def __init__(self, logger_name: str = "tiss_api"):
        self.logger = logging.getLogger(logger_name)
    
    def log_database_operation(self, operation: str, table: str, record_id: int = None, 
                              success: bool = True, error: str = None, duration: float = None):
        """Log database operations"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "type": "database_operation",
            "operation": operation,
            "table": table,
            "record_id": record_id,
            "success": success,
            "error": error,
            "duration": duration
        }
        
        if success:
            self.logger.info(
                f"Database {operation} on {table}" + (f" (ID: {record_id})" if record_id else ""),
                extra={"log_data": log_data}
            )
        else:
            self.logger.error(
                f"Database {operation} failed on {table}: {error}",
                extra={"log_data": log_data}
            )
    
    def log_xml_operation(self, operation: str, claim_id: int = None, 
                         success: bool = True, error: str = None, duration: float = None):
        """Log XML operations"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "type": "xml_operation",
            "operation": operation,
            "claim_id": claim_id,
            "success": success,
            "error": error,
            "duration": duration
        }
        
        if success:
            self.logger.info(
                f"XML {operation}" + (f" for claim {claim_id}" if claim_id else ""),
                extra={"log_data": log_data}
            )
        else:
            self.logger.error(
                f"XML {operation} failed" + (f" for claim {claim_id}" if claim_id else f": {error}"),
                extra={"log_data": log_data}
            )
    
    def log_validation_operation(self, operation: str, xml_size: int = None,
                               success: bool = True, error: str = None, duration: float = None):
        """Log validation operations"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "type": "validation_operation",
            "operation": operation,
            "xml_size": xml_size,
            "success": success,
            "error": error,
            "duration": duration
        }
        
        if success:
            self.logger.info(
                f"Validation {operation}" + (f" (XML size: {xml_size} bytes)" if xml_size else ""),
                extra={"log_data": log_data}
            )
        else:
            self.logger.error(
                f"Validation {operation} failed: {error}",
                extra={"log_data": log_data}
            )

# Global logger instance
request_logger = RequestLogger() 