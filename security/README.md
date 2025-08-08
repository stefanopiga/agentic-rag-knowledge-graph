# FisioRAG Security Suite

Enterprise-grade security hardening, vulnerability assessment, and compliance validation for healthcare AI applications.

## Overview

The FisioRAG Security Suite provides comprehensive security controls designed specifically for healthcare AI applications that must comply with GDPR, HIPAA, and SOC 2 requirements.

### Key Features

- **🔒 Enterprise Security Configuration** - Multi-level security policies (Basic → Healthcare)
- **🔍 Automated Vulnerability Scanning** - Comprehensive security assessment using multiple tools
- **📋 Compliance Validation** - GDPR, HIPAA, SOC 2 compliance checking and reporting
- **🛡️ Runtime Security Protection** - Advanced middleware with rate limiting and attack detection
- **📊 Security Monitoring** - Real-time security event tracking and alerting
- **🔧 Security Hardening** - Automated security configuration and remediation

## Quick Start

### 1. Run Comprehensive Security Audit

```bash
# Complete security assessment (recommended)
uv run python security/run_security_audit.py --comprehensive --environment production

# Quick vulnerability scan (5 minutes)
uv run python security/run_security_audit.py --vulnerability-scan

# Compliance assessment only
uv run python security/run_security_audit.py --compliance --regulations GDPR HIPAA
```

### 2. Security Configuration

```python
from security import SecurityHardening, SecurityLevel

# Initialize healthcare-grade security
security = SecurityHardening(SecurityLevel.HEALTHCARE)

# Generate security report
report = security.generate_security_report()
print(f"Security Level: {report['security_level']}")
```

### 3. Integrate Security Middleware

```python
from fastapi import FastAPI
from security import setup_security_middleware

app = FastAPI()

# Add enterprise security middleware
security_config, api_key_auth = setup_security_middleware(
    app, 
    SecurityLevel.HEALTHCARE
)
```

## Security Levels

### Healthcare (HIPAA + GDPR Compliant)
- **Password Policy**: 14+ chars, 60-day expiry, 3 failed attempts
- **Session Security**: 15-minute timeout, secure cookies
- **Rate Limiting**: 30 requests/minute
- **Audit Retention**: 7 years (2555 days)
- **Encryption**: End-to-end encryption required
- **Compliance**: Full GDPR + HIPAA compliance

### Enterprise (SOC 2 Compliant)  
- **Password Policy**: 12+ chars, 90-day expiry, 5 failed attempts
- **Session Security**: 30-minute timeout
- **Rate Limiting**: 60 requests/minute
- **Audit Retention**: 2 years
- **Encryption**: Data at rest and in transit

### Enhanced (Security-Focused)
- **Password Policy**: 10+ chars, 120-day expiry
- **Session Security**: 45-minute timeout
- **Rate Limiting**: 100 requests/minute
- **Compliance**: Basic data protection

### Basic (Development)
- **Password Policy**: Standard requirements
- **Session Security**: Standard timeouts
- **Rate Limiting**: Permissive limits
- **Compliance**: Minimal requirements

## Components

### 1. Security Configuration (`security_config.py`)

Centralized security policy management with environment-specific configurations.

```python
from security import get_security_config

# Get environment-specific configuration
config = get_security_config("production")  # Uses Healthcare level

# Password validation
result = config.validate_password_strength("MySecurePassword123!")
if result["valid"]:
    print("Password meets security requirements")

# Generate security headers
headers = config.get_security_headers()
```

### 2. Vulnerability Scanner (`vulnerability_scanner.py`)

Automated security vulnerability detection using multiple scanning tools:

- **Bandit** - Python code security analysis
- **Safety** - Known vulnerability detection in dependencies  
- **Semgrep** - Advanced static analysis
- **Docker/Trivy** - Container vulnerability scanning
- **API Security** - Endpoint security assessment
- **Configuration** - Security misconfigurations

```python
from security import VulnerabilityScanner

scanner = VulnerabilityScanner()
scan_result = await scanner.run_comprehensive_scan()

print(f"Vulnerabilities found: {scan_result.summary['total']}")
print(f"Critical/High: {scan_result.summary['critical'] + scan_result.summary['high']}")

# Export reports
json_report = scanner.export_results(scan_result, "json")
html_report = scanner.export_results(scan_result, "html")
```

### 3. Compliance Checker (`compliance_checker.py`)

Automated compliance validation for healthcare and data protection regulations:

#### GDPR Compliance
- Data encryption at rest and in transit
- Access logging and monitoring
- Data retention and deletion policies
- Consent management mechanisms
- Data portability features
- Privacy by design implementation

#### HIPAA Compliance  
- Administrative safeguards
- Physical safeguards
- Technical safeguards (access controls, audit logs, encryption)
- Information integrity controls
- Transmission security

#### SOC 2 Compliance
- Logical access controls
- Network security controls
- System monitoring and logging

```python
from security import ComplianceChecker

checker = ComplianceChecker(security_config)
report = await checker.run_compliance_assessment(["GDPR", "HIPAA", "SOC2"])

print(f"Overall compliance: {report.overall_score:.1%}")
for regulation, stats in report.summary['by_regulation'].items():
    print(f"{regulation}: {stats['compliance_rate']:.1%}")
```

### 4. Security Middleware (`security_middleware.py`)

Runtime security protection for FastAPI applications:

#### Features
- **Rate Limiting** - Per-IP and per-endpoint rate limiting with Redis backend
- **Attack Detection** - SQL injection, XSS, command injection pattern detection
- **Request Validation** - Size limits, content validation, suspicious pattern detection
- **IP Blocking** - Automatic temporary blocking of malicious IPs
- **Security Headers** - Comprehensive security headers (CSP, HSTS, etc.)
- **API Key Authentication** - Secure API key validation and management

```python
# Middleware automatically protects all endpoints
app.add_middleware(SecurityMiddleware, security_config=config)

# Access security metrics
security_metrics = middleware.get_security_metrics()
print(f"Security events (1h): {security_metrics['total_events_1h']}")
```

## Security Audit Reports

The security suite generates comprehensive reports in multiple formats:

### Vulnerability Assessment Report
- **Executive Summary** - High-level security posture assessment
- **Detailed Findings** - Complete vulnerability inventory with remediation guidance
- **Risk Analysis** - Prioritized risk assessment by severity and impact
- **Remediation Plan** - Step-by-step security improvement recommendations

### Compliance Assessment Report  
- **Regulatory Status** - Compliance score for each applicable regulation
- **Gap Analysis** - Specific areas requiring attention for compliance
- **Control Effectiveness** - Assessment of existing security controls
- **Remediation Roadmap** - Timeline and priorities for compliance improvements

### Security Configuration Report
- **Policy Assessment** - Current security policy effectiveness
- **Configuration Review** - Security settings validation
- **Best Practices** - Alignment with industry security standards
- **Hardening Recommendations** - Specific configuration improvements

## Security Event Monitoring

Real-time security event tracking and alerting:

```python
# Log security events
security_config.log_security_event("failed_login", {
    "ip_address": "192.168.1.100",
    "user_id": "user123",
    "attempts": 3
})

# Monitor security metrics
events = security_config.security_events
recent_events = [e for e in events if e.timestamp > datetime.now() - timedelta(hours=1)]
```

### Security Event Types
- **Authentication Failures** - Failed login attempts, invalid tokens
- **Attack Detection** - SQL injection, XSS, command injection attempts
- **Rate Limiting** - Requests exceeding rate limits
- **Suspicious Activity** - Unusual access patterns, privilege escalation attempts
- **System Security** - Configuration changes, security setting modifications

## Best Practices

### 1. Environment-Specific Security

```python
# Development
security_dev = get_security_config("development")  # Basic level

# Staging  
security_staging = get_security_config("staging")   # Enhanced level

# Production
security_prod = get_security_config("production")   # Healthcare level
```

### 2. Regular Security Assessments

```bash
# Schedule weekly vulnerability scans
0 2 * * 1 cd /app && uv run python security/run_security_audit.py --vulnerability-scan

# Monthly comprehensive audits
0 1 1 * * cd /app && uv run python security/run_security_audit.py --comprehensive
```

### 3. Continuous Monitoring

```python
# Continuous vulnerability monitoring
scanner = VulnerabilityScanner()
await scanner.continuous_monitoring(interval_hours=24)

# Security event monitoring
for event in security_config.security_events:
    if event.severity == "high":
        send_security_alert(event)
```

### 4. Compliance Maintenance

```python
# Quarterly compliance assessments
quarterly_assessment = await checker.run_compliance_assessment()

# Track compliance trends
compliance_history = checker.assessment_history
trend_analysis = analyze_compliance_trends(compliance_history)
```

## Integration Examples

### FastAPI Application Integration

```python
from fastapi import FastAPI
from security import setup_security_middleware, SecurityLevel

app = FastAPI()

# Setup enterprise security
security_config, api_key_auth = setup_security_middleware(
    app, 
    SecurityLevel.HEALTHCARE
)

# Protect specific endpoints
@app.post("/sensitive-data")
async def sensitive_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(api_key_auth)
):
    # Endpoint automatically protected with:
    # - Rate limiting
    # - Attack detection  
    # - Request validation
    # - Security headers
    return {"data": "protected"}
```

### Docker Integration

```dockerfile
# Add security scanning to Docker build
FROM python:3.11-slim

# Install security tools
RUN pip install bandit safety semgrep

# Copy security configuration
COPY security/ /app/security/

# Run security scan during build
RUN python security/run_security_audit.py --vulnerability-scan

# Configure security settings
ENV SECURITY_LEVEL=healthcare
ENV FORCE_HTTPS=true
ENV SESSION_TIMEOUT=15
```

### CI/CD Integration

```yaml
# GitHub Actions security pipeline
name: Security Assessment
on: [push, pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup UV
        uses: astral-sh/setup-uv@v6
        
      - name: Run Security Audit
        run: |
          uv run python security/run_security_audit.py --comprehensive
          
      - name: Upload Security Reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: security/reports/
```

## Troubleshooting

### Common Issues

**High False Positive Rate:**
```bash
# Configure scanner exclusions
export BANDIT_EXCLUDE="tests/,venv/"
export SAFETY_IGNORE="vulnerabilities.json"
```

**Rate Limiting Issues:**
```python
# Adjust rate limits for your use case
rate_limits = {
    "/api/bulk": RateLimitRule(10, 20, 60, 300),  # Lower for bulk operations
    "/api/search": RateLimitRule(100, 150, 60, 60)  # Higher for search
}
```

**Compliance Failures:**
```python
# Review specific compliance requirements
compliance_result = await checker._check_gdpr_encryption()
print(compliance_result.recommendations)
```

### Performance Optimization

**Scanner Performance:**
```python
# Run scanners in parallel for faster results
scanner = VulnerabilityScanner()
scan_result = await scanner.run_comprehensive_scan()  # Already parallelized
```

**Middleware Performance:**
```python
# Use Redis for better rate limiting performance
redis_client = redis.from_url("redis://localhost:6379")
middleware = SecurityMiddleware(app, security_config, redis_client)
```

## Support and Contributing

### Security Issues

For security vulnerabilities, please contact the security team directly rather than creating public issues.

### Documentation

- **Architecture**: See `docs/SECURITY_ARCHITECTURE.md`
- **Compliance**: See `docs/COMPLIANCE_GUIDE.md`  
- **API Reference**: See `docs/SECURITY_API.md`

### Contributing

1. Security changes require security team review
2. All security code must include comprehensive tests
3. Vulnerability scanner updates require validation against known CVEs
4. Compliance checker changes must be validated against regulation requirements

---

**Security Contact**: security@fisiorag.com  
**Emergency Security Issues**: Use encrypted communication channel
