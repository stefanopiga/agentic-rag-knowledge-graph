"""
Security middleware for FisioRAG FastAPI application.
Enterprise-grade security controls and request protection.
"""

import time
import json
import hashlib
import hmac
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set, Callable
from dataclasses import dataclass
import asyncio
from collections import defaultdict, deque

from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import redis

from .security_config import SecurityHardening, SecurityLevel


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""
    requests_per_minute: int
    burst_allowance: int
    window_seconds: int = 60
    block_duration_seconds: int = 300  # 5 minutes


@dataclass
class SecurityEvent:
    """Security event for monitoring."""
    timestamp: datetime
    event_type: str
    severity: str
    client_ip: str
    user_agent: str
    endpoint: str
    details: Dict[str, Any]


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware for FisioRAG.
    Implements rate limiting, request validation, and attack protection.
    """
    
    def __init__(
        self, 
        app: FastAPI, 
        security_config: SecurityHardening,
        redis_client: Optional[redis.Redis] = None
    ):
        super().__init__(app)
        self.security_config = security_config
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)
        
        # In-memory storage for rate limiting (fallback if Redis unavailable)
        self.rate_limit_storage: Dict[str, deque] = defaultdict(deque)
        self.blocked_ips: Dict[str, datetime] = {}
        
        # Security events storage
        self.security_events: deque = deque(maxlen=10000)
        
        # Rate limiting rules by endpoint
        self.rate_limits = {
            "/chat": RateLimitRule(30, 50, 60, 300),
            "/chat/stream": RateLimitRule(20, 30, 60, 300),
            "/search": RateLimitRule(60, 100, 60, 180),
            "/health": RateLimitRule(120, 200, 60, 60),
            "default": RateLimitRule(
                self.security_config.policy.rate_limit_requests_per_minute,
                self.security_config.policy.rate_limit_burst,
                60,
                300
            )
        }
        
        # Suspicious patterns for detection
        self.attack_patterns = [
            # SQL Injection patterns
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|OR|AND)\b.*['\";])",
            # XSS patterns
            r"(<script[^>]*>.*?</script>|javascript:|on\w+\s*=)",
            # Command injection patterns
            r"(;|\||\&)\s*(ls|cat|wget|curl|rm|mkdir|chmod)",
            # Path traversal
            r"(\.\./){2,}",
            # NoSQL injection
            r"(\$where|\$ne|\$gt|\$lt|\$regex)",
        ]
        
        # Compile regex patterns for performance
        import re
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.attack_patterns]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware processing."""
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        
        try:
            # 1. Check if IP is blocked
            if await self._is_ip_blocked(client_ip):
                return await self._create_blocked_response(client_ip)
            
            # 2. Rate limiting
            rate_limit_result = await self._check_rate_limit(request, client_ip)
            if not rate_limit_result["allowed"]:
                return await self._create_rate_limit_response(rate_limit_result)
            
            # 3. Request validation and attack detection
            attack_detected = await self._detect_attacks(request)
            if attack_detected:
                await self._log_security_event("attack_detected", "high", request, attack_detected)
                return await self._create_attack_response()
            
            # 4. Request size validation
            if not await self._validate_request_size(request):
                return await self._create_large_request_response()
            
            # 5. Process request
            response = await call_next(request)
            
            # 6. Add security headers
            response = await self._add_security_headers(response)
            
            # 7. Log successful request
            processing_time = time.time() - start_time
            await self._log_request(request, response, processing_time)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Security middleware error: {e}")
            await self._log_security_event("middleware_error", "high", request, {"error": str(e)})
            
            # Return safe error response
            return JSONResponse(
                status_code=500,
                content={"error": "Internal security error"},
                headers=self.security_config.get_security_headers()
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address safely."""
        # Check for forwarded headers (load balancer/proxy)
        forwarded_ips = request.headers.get("X-Forwarded-For")
        if forwarded_ips:
            # Take the first IP (original client)
            return forwarded_ips.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct connection
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
    
    async def _is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP address is currently blocked."""
        if self.redis_client:
            try:
                blocked_until = await self.redis_client.get(f"blocked_ip:{client_ip}")
                if blocked_until:
                    blocked_time = datetime.fromisoformat(blocked_until.decode())
                    return datetime.now() < blocked_time
            except Exception as e:
                self.logger.error(f"Redis IP block check failed: {e}")
        
        # Fallback to in-memory storage
        if client_ip in self.blocked_ips:
            return datetime.now() < self.blocked_ips[client_ip]
        
        return False
    
    async def _check_rate_limit(self, request: Request, client_ip: str) -> Dict[str, Any]:
        """Check rate limiting for client IP and endpoint."""
        endpoint = request.url.path
        rule = self.rate_limits.get(endpoint, self.rate_limits["default"])
        
        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=rule.window_seconds)
        
        # Use Redis if available
        if self.redis_client:
            try:
                return await self._redis_rate_limit(client_ip, endpoint, rule, current_time, window_start)
            except Exception as e:
                self.logger.error(f"Redis rate limiting failed: {e}")
        
        # Fallback to in-memory rate limiting
        return await self._memory_rate_limit(client_ip, endpoint, rule, current_time, window_start)
    
    async def _redis_rate_limit(self, client_ip: str, endpoint: str, rule: RateLimitRule, 
                               current_time: datetime, window_start: datetime) -> Dict[str, Any]:
        """Redis-based rate limiting."""
        key = f"rate_limit:{client_ip}:{endpoint}"
        
        # Use Redis sorted set for sliding window
        pipe = self.redis_client.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start.timestamp())
        
        # Count current requests
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(current_time.timestamp()): current_time.timestamp()})
        
        # Set expiration
        pipe.expire(key, rule.window_seconds)
        
        results = await pipe.execute()
        current_requests = results[1]
        
        allowed = current_requests < rule.requests_per_minute
        
        return {
            "allowed": allowed,
            "current_requests": current_requests,
            "limit": rule.requests_per_minute,
            "reset_time": current_time + timedelta(seconds=rule.window_seconds),
            "retry_after": rule.block_duration_seconds if not allowed else 0
        }
    
    async def _memory_rate_limit(self, client_ip: str, endpoint: str, rule: RateLimitRule,
                                current_time: datetime, window_start: datetime) -> Dict[str, Any]:
        """In-memory rate limiting fallback."""
        key = f"{client_ip}:{endpoint}"
        
        # Clean old entries
        if key in self.rate_limit_storage:
            while (self.rate_limit_storage[key] and 
                   self.rate_limit_storage[key][0] < window_start.timestamp()):
                self.rate_limit_storage[key].popleft()
        
        # Add current request
        self.rate_limit_storage[key].append(current_time.timestamp())
        
        current_requests = len(self.rate_limit_storage[key])
        allowed = current_requests <= rule.requests_per_minute
        
        return {
            "allowed": allowed,
            "current_requests": current_requests,
            "limit": rule.requests_per_minute,
            "reset_time": current_time + timedelta(seconds=rule.window_seconds),
            "retry_after": rule.block_duration_seconds if not allowed else 0
        }
    
    async def _detect_attacks(self, request: Request) -> Optional[Dict[str, Any]]:
        """Detect potential security attacks."""
        attack_details = {}
        
        # Check URL for malicious patterns
        url_str = str(request.url)
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(url_str):
                attack_details["url_pattern"] = i
                attack_details["matched_text"] = pattern.search(url_str).group()
                break
        
        # Check query parameters
        for key, value in request.query_params.items():
            for i, pattern in enumerate(self.compiled_patterns):
                if pattern.search(value):
                    attack_details["query_pattern"] = i
                    attack_details["parameter"] = key
                    attack_details["matched_text"] = pattern.search(value).group()
                    break
        
        # Check request body if present
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Read body safely
                body = await request.body()
                if body:
                    body_str = body.decode('utf-8', errors='ignore')
                    for i, pattern in enumerate(self.compiled_patterns):
                        if pattern.search(body_str):
                            attack_details["body_pattern"] = i
                            attack_details["matched_text"] = pattern.search(body_str).group()
                            break
            except Exception:
                # Body reading failed, continue
                pass
        
        # Check headers for suspicious content
        suspicious_headers = ["User-Agent", "Referer", "X-Forwarded-For"]
        for header in suspicious_headers:
            header_value = request.headers.get(header, "")
            for i, pattern in enumerate(self.compiled_patterns):
                if pattern.search(header_value):
                    attack_details["header_pattern"] = i
                    attack_details["header_name"] = header
                    attack_details["matched_text"] = pattern.search(header_value).group()
                    break
        
        return attack_details if attack_details else None
    
    async def _validate_request_size(self, request: Request) -> bool:
        """Validate request size to prevent DoS attacks."""
        max_size = 10 * 1024 * 1024  # 10MB limit
        
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                return size <= max_size
            except ValueError:
                return False
        
        return True
    
    async def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response."""
        security_headers = self.security_config.get_security_headers()
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response
    
    async def _log_security_event(self, event_type: str, severity: str, 
                                 request: Request, details: Dict[str, Any]):
        """Log security events."""
        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            client_ip=self._get_client_ip(request),
            user_agent=request.headers.get("User-Agent", "unknown"),
            endpoint=request.url.path,
            details=details
        )
        
        self.security_events.append(event)
        
        # Log to application logger
        self.logger.warning(f"Security Event: {event_type} - {severity} - {details}")
        
        # If high severity, consider blocking IP
        if severity == "high":
            await self._consider_ip_blocking(event.client_ip, event_type)
    
    async def _consider_ip_blocking(self, client_ip: str, event_type: str):
        """Consider blocking IP based on security events."""
        # Count recent events from this IP
        recent_events = [
            event for event in self.security_events
            if (event.client_ip == client_ip and 
                event.timestamp > datetime.now() - timedelta(minutes=10))
        ]
        
        # Block if too many high-severity events
        if len(recent_events) >= 3:
            await self._block_ip(client_ip, duration_minutes=30)
    
    async def _block_ip(self, client_ip: str, duration_minutes: int = 30):
        """Block IP address temporarily."""
        block_until = datetime.now() + timedelta(minutes=duration_minutes)
        
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    f"blocked_ip:{client_ip}",
                    duration_minutes * 60,
                    block_until.isoformat()
                )
            except Exception as e:
                self.logger.error(f"Redis IP blocking failed: {e}")
        
        # Also store in memory as fallback
        self.blocked_ips[client_ip] = block_until
        
        self.logger.warning(f"Blocked IP {client_ip} until {block_until}")
    
    async def _log_request(self, request: Request, response: Response, processing_time: float):
        """Log request for monitoring."""
        if request.url.path not in ["/health", "/metrics"]:  # Skip noise
            self.logger.info(
                f"{request.method} {request.url.path} "
                f"{response.status_code} {processing_time:.3f}s "
                f"IP:{self._get_client_ip(request)}"
            )
    
    async def _create_blocked_response(self, client_ip: str) -> JSONResponse:
        """Create response for blocked IP."""
        return JSONResponse(
            status_code=429,
            content={
                "error": "IP address temporarily blocked",
                "message": "Your IP has been temporarily blocked due to suspicious activity"
            },
            headers=self.security_config.get_security_headers()
        )
    
    async def _create_rate_limit_response(self, rate_limit_result: Dict[str, Any]) -> JSONResponse:
        """Create response for rate limit exceeded."""
        headers = self.security_config.get_security_headers()
        headers.update({
            "X-RateLimit-Limit": str(rate_limit_result["limit"]),
            "X-RateLimit-Remaining": str(max(0, rate_limit_result["limit"] - rate_limit_result["current_requests"])),
            "X-RateLimit-Reset": str(int(rate_limit_result["reset_time"].timestamp())),
            "Retry-After": str(rate_limit_result["retry_after"])
        })
        
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {rate_limit_result['limit']} per minute"
            },
            headers=headers
        )
    
    async def _create_attack_response(self) -> JSONResponse:
        """Create response for detected attack."""
        return JSONResponse(
            status_code=400,
            content={
                "error": "Request blocked",
                "message": "Request contains potentially malicious content"
            },
            headers=self.security_config.get_security_headers()
        )
    
    async def _create_large_request_response(self) -> JSONResponse:
        """Create response for oversized request."""
        return JSONResponse(
            status_code=413,
            content={
                "error": "Request too large",
                "message": "Request size exceeds maximum allowed limit"
            },
            headers=self.security_config.get_security_headers()
        )
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics for monitoring."""
        recent_events = [
            event for event in self.security_events
            if event.timestamp > datetime.now() - timedelta(hours=1)
        ]
        
        event_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for event in recent_events:
            event_counts[event.event_type] += 1
            severity_counts[event.severity] += 1
        
        return {
            "total_events_1h": len(recent_events),
            "event_types": dict(event_counts),
            "severity_counts": dict(severity_counts),
            "blocked_ips_count": len([ip for ip, until in self.blocked_ips.items() 
                                    if until > datetime.now()]),
            "rate_limit_storage_size": len(self.rate_limit_storage)
        }


class APIKeyAuth(HTTPBearer):
    """
    API Key authentication for FisioRAG.
    Validates API keys and manages access control.
    """
    
    def __init__(self, security_config: SecurityHardening, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.security_config = security_config
        self.logger = logging.getLogger(__name__)
        
        # In production, these would be stored in a secure database
        self.valid_api_keys: Set[str] = set()
        self.api_key_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        """Validate API key authentication."""
        credentials = await super().__call__(request)
        
        if not credentials:
            return None
        
        # Validate API key format
        if not self.security_config.validate_api_key(credentials.credentials):
            self.logger.warning(f"Invalid API key format from {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key format"
            )
        
        # Check if API key exists and is valid
        if not await self._validate_api_key(credentials.credentials, request):
            self.logger.warning(f"Invalid API key attempted from {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        return credentials
    
    async def _validate_api_key(self, api_key: str, request: Request) -> bool:
        """Validate API key against database/storage."""
        # In production, check against secure database
        # For now, validate against in-memory store
        
        if api_key not in self.valid_api_keys:
            return False
        
        # Check API key metadata (rate limits, permissions, expiration)
        metadata = self.api_key_metadata.get(api_key, {})
        
        # Check expiration
        if "expires_at" in metadata:
            expires_at = datetime.fromisoformat(metadata["expires_at"])
            if datetime.now() > expires_at:
                self.logger.info(f"Expired API key used: {api_key[:8]}...")
                return False
        
        # Log API key usage
        self.logger.info(f"Valid API key used: {api_key[:8]}... from {request.client.host}")
        
        return True
    
    def add_api_key(self, api_key: str, metadata: Optional[Dict[str, Any]] = None):
        """Add valid API key."""
        self.valid_api_keys.add(api_key)
        if metadata:
            self.api_key_metadata[api_key] = metadata
    
    def revoke_api_key(self, api_key: str):
        """Revoke API key."""
        self.valid_api_keys.discard(api_key)
        self.api_key_metadata.pop(api_key, None)


def setup_security_middleware(app: FastAPI, security_level: SecurityLevel = SecurityLevel.HEALTHCARE):
    """Setup security middleware for FastAPI application."""
    security_config = SecurityHardening(security_level)
    
    # Try to initialize Redis client
    redis_client = None
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url, decode_responses=True)
        # Test connection
        redis_client.ping()
        logging.info("Redis connected for security middleware")
    except Exception as e:
        logging.warning(f"Redis not available for security middleware: {e}")
    
    # Add security middleware
    app.add_middleware(SecurityMiddleware, security_config=security_config, redis_client=redis_client)
    
    # Setup API key authentication
    api_key_auth = APIKeyAuth(security_config)
    
    return security_config, api_key_auth
