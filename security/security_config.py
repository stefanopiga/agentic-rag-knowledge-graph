"""
Security configuration and hardening for FisioRAG production deployment.
Enterprise-grade security controls and compliance standards.
"""

import os
import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re


class SecurityLevel(Enum):
    """Security compliance levels."""
    BASIC = "basic"
    ENHANCED = "enhanced"
    ENTERPRISE = "enterprise"
    HEALTHCARE = "healthcare"  # HIPAA/GDPR compliant


@dataclass
class SecurityPolicy:
    """Security policy configuration."""
    
    # Authentication settings
    password_min_length: int = 12
    password_require_special: bool = True
    password_require_numbers: bool = True
    password_require_uppercase: bool = True
    password_max_age_days: int = 90
    login_attempt_limit: int = 5
    account_lockout_duration_minutes: int = 30
    
    # Session management
    session_timeout_minutes: int = 30
    session_absolute_timeout_hours: int = 8
    secure_cookies: bool = True
    session_regeneration_interval_minutes: int = 15
    
    # API security
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst: int = 100
    api_key_rotation_days: int = 30
    cors_allowed_origins: List[str] = None
    
    # Data protection
    encrypt_sensitive_data: bool = True
    data_retention_days: int = 365
    audit_log_retention_days: int = 2555  # 7 years for healthcare
    backup_encryption: bool = True
    
    # Network security
    force_https: bool = True
    hsts_max_age_seconds: int = 31536000  # 1 year
    content_security_policy_enabled: bool = True
    
    # Compliance
    gdpr_compliance: bool = True
    hipaa_compliance: bool = True
    data_anonymization: bool = True
    
    def __post_init__(self):
        """Initialize default values."""
        if self.cors_allowed_origins is None:
            self.cors_allowed_origins = []


class SecurityHardening:
    """
    Comprehensive security hardening implementation.
    Implements enterprise-grade security controls for FisioRAG.
    """
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.HEALTHCARE):
        self.security_level = security_level
        self.policy = self._get_policy_for_level(security_level)
        self.logger = logging.getLogger(__name__)
        
        # Security metrics
        self.security_events: List[Dict[str, Any]] = []
        self.vulnerability_scan_results: Dict[str, Any] = {}
        
    def _get_policy_for_level(self, level: SecurityLevel) -> SecurityPolicy:
        """Get security policy based on compliance level."""
        if level == SecurityLevel.HEALTHCARE:
            return SecurityPolicy(
                password_min_length=14,
                password_max_age_days=60,
                login_attempt_limit=3,
                account_lockout_duration_minutes=60,
                session_timeout_minutes=15,
                rate_limit_requests_per_minute=30,
                audit_log_retention_days=2555,  # 7 years
                gdpr_compliance=True,
                hipaa_compliance=True
            )
        elif level == SecurityLevel.ENTERPRISE:
            return SecurityPolicy(
                password_min_length=12,
                password_max_age_days=90,
                login_attempt_limit=5,
                session_timeout_minutes=30,
                rate_limit_requests_per_minute=60
            )
        elif level == SecurityLevel.ENHANCED:
            return SecurityPolicy(
                password_min_length=10,
                password_max_age_days=120,
                login_attempt_limit=7,
                session_timeout_minutes=45,
                rate_limit_requests_per_minute=100
            )
        else:  # BASIC
            return SecurityPolicy()
    
    def generate_secure_key(self, length: int = 32) -> str:
        """Generate cryptographically secure random key."""
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash password with salt using PBKDF2."""
        if salt is None:
            salt = secrets.token_hex(16)
        
        key = hashlib.pbkdf2_hmac('sha256', 
                                 password.encode('utf-8'), 
                                 salt.encode('utf-8'), 
                                 100000)  # 100k iterations
        return key.hex(), salt
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password against security policy."""
        result = {
            "valid": True,
            "score": 0,
            "feedback": [],
            "requirements_met": {}
        }
        
        # Length check
        length_ok = len(password) >= self.policy.password_min_length
        result["requirements_met"]["length"] = length_ok
        if not length_ok:
            result["feedback"].append(f"Password must be at least {self.policy.password_min_length} characters")
            result["valid"] = False
        else:
            result["score"] += 25
        
        # Special characters
        if self.policy.password_require_special:
            special_ok = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
            result["requirements_met"]["special_chars"] = special_ok
            if not special_ok:
                result["feedback"].append("Password must contain special characters")
                result["valid"] = False
            else:
                result["score"] += 25
        
        # Numbers
        if self.policy.password_require_numbers:
            numbers_ok = bool(re.search(r'\d', password))
            result["requirements_met"]["numbers"] = numbers_ok
            if not numbers_ok:
                result["feedback"].append("Password must contain numbers")
                result["valid"] = False
            else:
                result["score"] += 25
        
        # Uppercase
        if self.policy.password_require_uppercase:
            upper_ok = bool(re.search(r'[A-Z]', password))
            result["requirements_met"]["uppercase"] = upper_ok
            if not upper_ok:
                result["feedback"].append("Password must contain uppercase letters")
                result["valid"] = False
            else:
                result["score"] += 25
        
        # Common password patterns
        common_patterns = [
            r'(.)\\1{2,}',  # Repeated characters
            r'123|abc|qwe|password|admin|fisio',  # Common sequences
            r'^[a-zA-Z]+$',  # Only letters
            r'^[0-9]+$'      # Only numbers
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                result["feedback"].append("Password contains common patterns")
                result["score"] = max(0, result["score"] - 15)
                break
        
        return result
    
    def generate_csp_header(self) -> str:
        """Generate Content Security Policy header."""
        if not self.policy.content_security_policy_enabled:
            return ""
        
        directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",  # Adjust for React
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self'",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        
        return "; ".join(directives)
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get comprehensive security headers."""
        headers = {}
        
        if self.policy.force_https:
            headers["Strict-Transport-Security"] = f"max-age={self.policy.hsts_max_age_seconds}; includeSubDomains"
        
        headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        })
        
        csp = self.generate_csp_header()
        if csp:
            headers["Content-Security-Policy"] = csp
        
        return headers
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security events for monitoring."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "level": self.security_level.value,
            "details": details,
            "ip_address": details.get("ip_address", "unknown"),
            "user_id": details.get("user_id", "anonymous")
        }
        
        self.security_events.append(event)
        self.logger.warning(f"Security Event: {event_type} - {details}")
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key format and strength."""
        if not api_key or len(api_key) < 32:
            return False
        
        # Check for sufficient entropy
        unique_chars = len(set(api_key))
        if unique_chars < 16:  # Too predictable
            return False
        
        return True
    
    def sanitize_user_input(self, user_input: str) -> str:
        """Sanitize user input to prevent XSS and injection attacks."""
        if not user_input:
            return ""
        
        # Remove or escape dangerous characters
        sanitized = user_input.strip()
        
        # Remove script tags
        sanitized = re.sub(r'<script.*?>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove dangerous HTML tags
        dangerous_tags = ['script', 'iframe', 'object', 'embed', 'link', 'meta']
        for tag in dangerous_tags:
            sanitized = re.sub(f'<{tag}.*?>', '', sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(f'</{tag}>', '', sanitized, flags=re.IGNORECASE)
        
        # Escape remaining HTML
        sanitized = sanitized.replace('<', '&lt;').replace('>', '&gt;')
        
        return sanitized
    
    def check_rate_limit(self, identifier: str, current_time: datetime) -> tuple[bool, int]:
        """Check if request is within rate limits."""
        # In production, this would use Redis or similar
        # For now, implement basic in-memory rate limiting
        
        window_minutes = 1
        max_requests = self.policy.rate_limit_requests_per_minute
        
        # This is a simplified implementation
        # Production should use sliding window or token bucket
        return True, max_requests  # Placeholder
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security status report."""
        return {
            "security_level": self.security_level.value,
            "policy_summary": {
                "password_requirements": {
                    "min_length": self.policy.password_min_length,
                    "complexity_required": self.policy.password_require_special,
                    "max_age_days": self.policy.password_max_age_days
                },
                "session_security": {
                    "timeout_minutes": self.policy.session_timeout_minutes,
                    "secure_cookies": self.policy.secure_cookies
                },
                "api_protection": {
                    "rate_limit_rpm": self.policy.rate_limit_requests_per_minute,
                    "cors_configured": bool(self.policy.cors_allowed_origins)
                },
                "compliance": {
                    "gdpr_enabled": self.policy.gdpr_compliance,
                    "hipaa_enabled": self.policy.hipaa_compliance,
                    "data_encryption": self.policy.encrypt_sensitive_data
                }
            },
            "security_events_count": len(self.security_events),
            "last_vulnerability_scan": self.vulnerability_scan_results.get("last_scan"),
            "recommendations": self._generate_security_recommendations()
        }
    
    def _generate_security_recommendations(self) -> List[str]:
        """Generate security improvement recommendations."""
        recommendations = []
        
        if self.security_level == SecurityLevel.BASIC:
            recommendations.append("Consider upgrading to Enhanced or Enterprise security level")
        
        if not self.policy.encrypt_sensitive_data:
            recommendations.append("Enable encryption for sensitive data at rest")
        
        if not self.policy.force_https:
            recommendations.append("Enforce HTTPS for all communications")
        
        if self.policy.session_timeout_minutes > 30:
            recommendations.append("Consider reducing session timeout for better security")
        
        if len(self.security_events) > 100:
            recommendations.append("High number of security events detected - review logs")
        
        return recommendations


# Default security configuration for FisioRAG
DEFAULT_SECURITY_CONFIG = SecurityHardening(SecurityLevel.HEALTHCARE)

# Environment-specific configurations
SECURITY_CONFIGS = {
    "development": SecurityHardening(SecurityLevel.BASIC),
    "staging": SecurityHardening(SecurityLevel.ENHANCED),
    "production": SecurityHardening(SecurityLevel.HEALTHCARE)
}


def get_security_config(environment: str = None) -> SecurityHardening:
    """Get security configuration for environment."""
    if environment is None:
        environment = os.getenv("APP_ENV", "development")
    
    return SECURITY_CONFIGS.get(environment, DEFAULT_SECURITY_CONFIG)


def validate_environment_security() -> Dict[str, Any]:
    """Validate current environment security configuration."""
    env = os.getenv("APP_ENV", "development")
    config = get_security_config(env)
    
    checks = {
        "environment": env,
        "security_level": config.security_level.value,
        "https_enforced": config.policy.force_https,
        "session_security": config.policy.secure_cookies,
        "data_encryption": config.policy.encrypt_sensitive_data,
        "compliance_ready": config.policy.gdpr_compliance and config.policy.hipaa_compliance,
        "recommendations": config._generate_security_recommendations()
    }
    
    return checks
