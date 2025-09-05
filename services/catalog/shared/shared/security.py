import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import logging
from fastapi import HTTPException, Request
import redis
import json

logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.rate_limit_window = 60  # seconds
        self.max_requests_per_window = 100
        
    def generate_csrf_token(self, user_id: str) -> str:
        """Generate CSRF token for user"""
        token = secrets.token_urlsafe(32)
        key = f"csrf:{user_id}:{token}"
        self.redis.setex(key, 3600, "1")  # 1 hour expiry
        return token
    
    def validate_csrf_token(self, user_id: str, token: str) -> bool:
        """Validate CSRF token"""
        key = f"csrf:{user_id}:{token}"
        return self.redis.exists(key) > 0
    
    def rate_limit_check(self, client_ip: str, endpoint: str) -> bool:
        """Check if client is within rate limits"""
        key = f"rate_limit:{client_ip}:{endpoint}"
        current_requests = self.redis.incr(key)
        
        if current_requests == 1:
            self.redis.expire(key, self.rate_limit_window)
        
        return current_requests <= self.max_requests_per_window
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security events for monitoring"""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "details": details
        }
        
        # Store in Redis for real-time monitoring
        self.redis.lpush("security_events", json.dumps(event))
        self.redis.ltrim("security_events", 0, 1000)  # Keep last 1000 events
        
        logger.warning(f"Security event: {event_type} - {details}")

class InputSanitizer:
    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        """Sanitize string input"""
        if not value:
            return ""
        
        # Remove null bytes and control characters
        sanitized = "".join(char for char in value if ord(char) >= 32 or char in "\t\n\r")
        
        # Limit length
        return sanitized[:max_length].strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        import re
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        # Check if it's a valid length (7-15 digits)
        return 7 <= len(digits) <= 15

class SecurityHeaders:
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get security headers for responses"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }

class AuditLogger:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def log_user_action(self, user_id: str, action: str, resource: str, details: Dict[str, Any] = None):
        """Log user actions for audit trail"""
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "details": details or {},
            "ip_address": "unknown"  # Will be set by middleware
        }
        
        # Store in Redis
        self.redis.lpush("audit_log", json.dumps(audit_entry))
        self.redis.ltrim("audit_log", 0, 10000)  # Keep last 10k entries
        
        logger.info(f"Audit: User {user_id} performed {action} on {resource}")

# Security middleware
async def security_middleware(request: Request, call_next):
    """Security middleware for all requests"""
    security_manager = SecurityManager(redis.from_url(os.getenv("REDIS_URL")))
    audit_logger = AuditLogger(redis.from_url(os.getenv("REDIS_URL")))
    
    # Get client IP
    client_ip = request.client.host
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
    
    # Rate limiting
    endpoint = f"{request.method}:{request.url.path}"
    if not security_manager.rate_limit_check(client_ip, endpoint):
        security_manager.log_security_event("rate_limit_exceeded", {
            "ip": client_ip,
            "endpoint": endpoint
        })
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Process request
    response = await call_next(request)
    
    # Add security headers
    for header, value in SecurityHeaders.get_security_headers().items():
        response.headers[header] = value
    
    # Log security events for 4xx and 5xx responses
    if response.status_code >= 400:
        security_manager.log_security_event("http_error", {
            "status_code": response.status_code,
            "ip": client_ip,
            "endpoint": endpoint,
            "user_agent": request.headers.get("user-agent", "unknown")
        })
    
    return response
