from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os
from datetime import datetime, timedelta
import hashlib
import hmac

# Security scheme for API key authentication
security = HTTPBearer(auto_error=False)

class APIKeyAuth:
    """API Key Authentication middleware"""
    
    def __init__(self):
        # Get API key from environment variable
        self.api_key = os.getenv("API_KEY", "default-secure-api-key-2024")
        self.api_key_header = "X-API-Key"
        
        # Optional: Store valid API keys in a set for multiple keys
        self.valid_api_keys = {
            self.api_key,
            os.getenv("API_KEY_SECONDARY", "secondary-api-key-2024"),
            os.getenv("API_KEY_ADMIN", "admin-api-key-2024")
        }
        
        # Rate limiting settings
        self.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hour
        
        # Store rate limiting data (in production, use Redis)
        self.rate_limit_data = {}
    
    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate the provided API key
        
        Args:
            api_key: The API key to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not api_key:
            return False
        
        # Check if API key is in valid keys
        return api_key in self.valid_api_keys
    
    def check_rate_limit(self, client_ip: str, api_key: str) -> bool:
        """
        Check if the client has exceeded rate limits
        
        Args:
            client_ip: Client IP address
            api_key: API key used for authentication
            
        Returns:
            bool: True if within rate limit, False if exceeded
        """
        current_time = datetime.now()
        key = f"{client_ip}:{api_key}"
        
        # Clean old entries
        if key in self.rate_limit_data:
            old_time, count = self.rate_limit_data[key]
            if (current_time - old_time).total_seconds() > self.rate_limit_window:
                # Reset counter for new window
                self.rate_limit_data[key] = (current_time, 1)
                return True
        
        # Initialize or increment counter
        if key not in self.rate_limit_data:
            self.rate_limit_data[key] = (current_time, 1)
        else:
            old_time, count = self.rate_limit_data[key]
            if (current_time - old_time).total_seconds() <= self.rate_limit_window:
                if count >= self.rate_limit_requests:
                    return False
                self.rate_limit_data[key] = (old_time, count + 1)
        
        return True
    
    def get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request
        
        Args:
            request: FastAPI request object
            
        Returns:
            str: Client IP address
        """
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
    
    async def authenticate(self, request: Request) -> dict:
        """
        Authenticate the request using API key
        
        Args:
            request: FastAPI request object
            
        Returns:
            dict: Authentication result with user info
            
        Raises:
            HTTPException: If authentication fails
        """
        # Get API key from header
        api_key = request.headers.get(self.api_key_header)
        
        # Also check Authorization header as fallback
        if not api_key:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                api_key = auth_header[7:]  # Remove "Bearer " prefix
        
        # Validate API key
        if not self.validate_api_key(api_key):
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key",
                headers={"WWW-Authenticate": f"{self.api_key_header}"}
            )
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Check rate limiting
        if not self.check_rate_limit(client_ip, api_key):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "X-RateLimit-Limit": str(self.rate_limit_requests),
                    "X-RateLimit-Window": str(self.rate_limit_window),
                    "Retry-After": str(self.rate_limit_window)
                }
            )
        
        # Return authentication info
        return {
            "authenticated": True,
            "api_key": api_key,
            "client_ip": client_ip,
            "timestamp": datetime.now().isoformat(),
            "rate_limit_remaining": self._get_remaining_requests(client_ip, api_key)
        }
    
    def _get_remaining_requests(self, client_ip: str, api_key: str) -> int:
        """Get remaining requests for rate limiting"""
        key = f"{client_ip}:{api_key}"
        if key in self.rate_limit_data:
            _, count = self.rate_limit_data[key]
            return max(0, self.rate_limit_requests - count)
        return self.rate_limit_requests

# Global instance
auth_middleware = APIKeyAuth()

async def get_current_user(request: Request) -> dict:
    """
    Dependency to get current authenticated user
    
    Args:
        request: FastAPI request object
        
    Returns:
        dict: Authentication result
    """
    return await auth_middleware.authenticate(request)

async def require_auth(request: Request) -> dict:
    """
    Dependency that requires authentication
    
    Args:
        request: FastAPI request object
        
    Returns:
        dict: Authentication result
        
    Raises:
        HTTPException: If not authenticated
    """
    return await auth_middleware.authenticate(request)

def get_auth_headers(request: Request) -> dict:
    """
    Get authentication headers for response
    
    Args:
        request: FastAPI request object
        
    Returns:
        dict: Headers to include in response
    """
    client_ip = auth_middleware.get_client_ip(request)
    api_key = request.headers.get(auth_middleware.api_key_header, "")
    
    remaining = auth_middleware._get_remaining_requests(client_ip, api_key)
    
    return {
        "X-RateLimit-Limit": str(auth_middleware.rate_limit_requests),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Window": str(auth_middleware.rate_limit_window)
    } 