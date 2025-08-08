"""
FisioRAG Security Suite.

Enterprise-grade security hardening, vulnerability assessment, and compliance validation.
"""

__version__ = "1.0.0"
__author__ = "FisioRAG Security Team"

from .security_config import (
    SecurityHardening,
    SecurityLevel,
    SecurityPolicy,
    get_security_config,
    validate_environment_security
)

from .vulnerability_scanner import (
    VulnerabilityScanner,
    Vulnerability,
    ScanResult
)

from .compliance_checker import (
    ComplianceChecker,
    ComplianceRule,
    ComplianceResult,
    ComplianceReport
)

from .security_middleware import (
    SecurityMiddleware,
    APIKeyAuth,
    setup_security_middleware
)

__all__ = [
    # Configuration
    "SecurityHardening",
    "SecurityLevel", 
    "SecurityPolicy",
    "get_security_config",
    "validate_environment_security",
    
    # Vulnerability Scanning
    "VulnerabilityScanner",
    "Vulnerability",
    "ScanResult",
    
    # Compliance
    "ComplianceChecker",
    "ComplianceRule",
    "ComplianceResult", 
    "ComplianceReport",
    
    # Middleware
    "SecurityMiddleware",
    "APIKeyAuth",
    "setup_security_middleware"
]
