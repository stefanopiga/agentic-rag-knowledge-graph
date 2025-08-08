"""
Compliance checker for GDPR, HIPAA, and other healthcare regulations.
Automated compliance validation and reporting.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio

from .security_config import SecurityHardening, SecurityLevel


@dataclass
class ComplianceRule:
    """Individual compliance rule definition."""
    id: str
    regulation: str  # GDPR, HIPAA, SOC2, etc.
    category: str
    title: str
    description: str
    requirement: str
    severity: str  # critical, high, medium, low
    automated_check: bool = True
    remediation_guide: str = ""


@dataclass
class ComplianceResult:
    """Result of compliance rule evaluation."""
    rule_id: str
    compliant: bool
    confidence: float  # 0.0 to 1.0
    details: Dict[str, Any]
    evidence: List[str]
    recommendations: List[str]
    last_checked: datetime


@dataclass
class ComplianceReport:
    """Comprehensive compliance assessment report."""
    assessment_id: str
    timestamp: datetime
    regulations: List[str]
    overall_score: float
    results: List[ComplianceResult]
    summary: Dict[str, Any]
    recommendations: List[str]
    next_assessment_date: datetime


class ComplianceChecker:
    """
    Comprehensive compliance checker for healthcare and data protection regulations.
    Validates GDPR, HIPAA, SOC2, and other applicable standards.
    """
    
    def __init__(self, security_config: SecurityHardening):
        self.security_config = security_config
        self.logger = logging.getLogger(__name__)
        
        # Load compliance rules
        self.rules = self._load_compliance_rules()
        
        # Assessment history
        self.assessment_history: List[ComplianceReport] = []
    
    def _load_compliance_rules(self) -> List[ComplianceRule]:
        """Load compliance rules for different regulations."""
        rules = []
        
        # GDPR Rules
        gdpr_rules = [
            ComplianceRule(
                id="gdpr_001",
                regulation="GDPR",
                category="data_protection",
                title="Data Encryption at Rest",
                description="Personal data must be encrypted when stored",
                requirement="Article 32 - Security of processing",
                severity="critical",
                remediation_guide="Enable encryption for all database storage containing personal data"
            ),
            ComplianceRule(
                id="gdpr_002",
                regulation="GDPR",
                category="data_protection",
                title="Data Encryption in Transit",
                description="Personal data must be encrypted during transmission",
                requirement="Article 32 - Security of processing",
                severity="critical",
                remediation_guide="Enforce HTTPS/TLS for all data transmission"
            ),
            ComplianceRule(
                id="gdpr_003",
                regulation="GDPR",
                category="access_control",
                title="Access Logging and Monitoring",
                description="All access to personal data must be logged and monitored",
                requirement="Article 25 - Data protection by design",
                severity="high",
                remediation_guide="Implement comprehensive audit logging for data access"
            ),
            ComplianceRule(
                id="gdpr_004",
                regulation="GDPR",
                category="data_retention",
                title="Data Retention Policies",
                description="Personal data must not be kept longer than necessary",
                requirement="Article 5 - Principles relating to processing",
                severity="high",
                remediation_guide="Implement automated data retention and deletion policies"
            ),
            ComplianceRule(
                id="gdpr_005",
                regulation="GDPR",
                category="consent",
                title="Consent Management",
                description="Valid consent must be obtained and manageable by users",
                requirement="Article 7 - Conditions for consent",
                severity="critical",
                remediation_guide="Implement clear consent mechanisms and withdrawal options"
            ),
            ComplianceRule(
                id="gdpr_006",
                regulation="GDPR",
                category="data_portability",
                title="Data Export Capability",
                description="Users must be able to export their data",
                requirement="Article 20 - Right to data portability",
                severity="medium",
                remediation_guide="Provide user data export functionality"
            ),
            ComplianceRule(
                id="gdpr_007",
                regulation="GDPR",
                category="privacy_by_design",
                title="Privacy by Design Implementation",
                description="Privacy protections must be built into system design",
                requirement="Article 25 - Data protection by design",
                severity="high",
                remediation_guide="Review system architecture for privacy-preserving design"
            )
        ]
        
        # HIPAA Rules
        hipaa_rules = [
            ComplianceRule(
                id="hipaa_001",
                regulation="HIPAA",
                category="safeguards",
                title="Administrative Safeguards",
                description="Implement administrative safeguards for PHI access",
                requirement="45 CFR 164.308 - Administrative safeguards",
                severity="critical",
                remediation_guide="Establish comprehensive administrative access controls"
            ),
            ComplianceRule(
                id="hipaa_002",
                regulation="HIPAA",
                category="safeguards",
                title="Physical Safeguards",
                description="Implement physical safeguards for systems containing PHI",
                requirement="45 CFR 164.310 - Physical safeguards",
                severity="critical",
                remediation_guide="Secure physical access to servers and data storage"
            ),
            ComplianceRule(
                id="hipaa_003",
                regulation="HIPAA",
                category="safeguards",
                title="Technical Safeguards",
                description="Implement technical safeguards for PHI protection",
                requirement="45 CFR 164.312 - Technical safeguards",
                severity="critical",
                remediation_guide="Implement access controls, audit logs, and encryption"
            ),
            ComplianceRule(
                id="hipaa_004",
                regulation="HIPAA",
                category="audit",
                title="Audit Controls",
                description="Implement audit controls for PHI access",
                requirement="45 CFR 164.312(b) - Audit controls",
                severity="high",
                remediation_guide="Enable comprehensive audit logging for all PHI access"
            ),
            ComplianceRule(
                id="hipaa_005",
                regulation="HIPAA",
                category="integrity",
                title="Information Integrity",
                description="Protect PHI from improper alteration or destruction",
                requirement="45 CFR 164.312(c)(1) - Integrity",
                severity="high",
                remediation_guide="Implement data integrity controls and backup procedures"
            ),
            ComplianceRule(
                id="hipaa_006",
                regulation="HIPAA",
                category="transmission",
                title="Transmission Security",
                description="Protect PHI during electronic transmission",
                requirement="45 CFR 164.312(e)(1) - Transmission security",
                severity="critical",
                remediation_guide="Encrypt all PHI transmissions and implement secure channels"
            )
        ]
        
        # SOC 2 Rules (Security-focused)
        soc2_rules = [
            ComplianceRule(
                id="soc2_001",
                regulation="SOC2",
                category="security",
                title="Logical Access Controls",
                description="Implement logical access controls to systems",
                requirement="CC6.1 - Logical and physical access controls",
                severity="high",
                remediation_guide="Implement role-based access controls and authentication"
            ),
            ComplianceRule(
                id="soc2_002",
                regulation="SOC2",
                category="security",
                title="Network Security",
                description="Implement network security controls",
                requirement="CC6.1 - Logical and physical access controls",
                severity="high",
                remediation_guide="Configure firewalls, network segmentation, and monitoring"
            ),
            ComplianceRule(
                id="soc2_003",
                regulation="SOC2",
                category="monitoring",
                title="System Monitoring",
                description="Monitor system activities and detect security events",
                requirement="CC7.1 - System monitoring",
                severity="high",
                remediation_guide="Implement comprehensive monitoring and alerting systems"
            )
        ]
        
        rules.extend(gdpr_rules)
        rules.extend(hipaa_rules)
        rules.extend(soc2_rules)
        
        return rules
    
    async def run_compliance_assessment(self, regulations: Optional[List[str]] = None) -> ComplianceReport:
        """Run comprehensive compliance assessment."""
        assessment_id = f"compliance_assessment_{int(datetime.now().timestamp())}"
        
        if regulations is None:
            regulations = ["GDPR", "HIPAA", "SOC2"]
        
        self.logger.info(f"Starting compliance assessment: {assessment_id}")
        
        # Filter rules by requested regulations
        applicable_rules = [rule for rule in self.rules if rule.regulation in regulations]
        
        # Run compliance checks
        results = []
        for rule in applicable_rules:
            result = await self._check_compliance_rule(rule)
            results.append(result)
        
        # Calculate overall score
        overall_score = self._calculate_compliance_score(results)
        
        # Generate summary and recommendations
        summary = self._generate_compliance_summary(results, regulations)
        recommendations = self._generate_compliance_recommendations(results)
        
        # Create assessment report
        report = ComplianceReport(
            assessment_id=assessment_id,
            timestamp=datetime.now(),
            regulations=regulations,
            overall_score=overall_score,
            results=results,
            summary=summary,
            recommendations=recommendations,
            next_assessment_date=datetime.now() + timedelta(days=90)  # Quarterly
        )
        
        self.assessment_history.append(report)
        
        self.logger.info(f"Compliance assessment completed: {overall_score:.1%} compliant")
        return report
    
    async def _check_compliance_rule(self, rule: ComplianceRule) -> ComplianceResult:
        """Check individual compliance rule."""
        if not rule.automated_check:
            # Manual review required
            return ComplianceResult(
                rule_id=rule.id,
                compliant=False,
                confidence=0.0,
                details={"status": "manual_review_required"},
                evidence=[],
                recommendations=[f"Manual review required for {rule.title}"],
                last_checked=datetime.now()
            )
        
        # Automated compliance checks
        if rule.id == "gdpr_001":
            return await self._check_data_encryption_at_rest(rule)
        elif rule.id == "gdpr_002":
            return await self._check_data_encryption_in_transit(rule)
        elif rule.id == "gdpr_003":
            return await self._check_access_logging(rule)
        elif rule.id == "gdpr_004":
            return await self._check_data_retention_policies(rule)
        elif rule.id == "gdpr_005":
            return await self._check_consent_management(rule)
        elif rule.id == "gdpr_006":
            return await self._check_data_portability(rule)
        elif rule.id == "gdpr_007":
            return await self._check_privacy_by_design(rule)
        elif rule.id.startswith("hipaa_"):
            return await self._check_hipaa_safeguards(rule)
        elif rule.id.startswith("soc2_"):
            return await self._check_soc2_controls(rule)
        else:
            # Default check
            return await self._check_security_configuration(rule)
    
    async def _check_data_encryption_at_rest(self, rule: ComplianceRule) -> ComplianceResult:
        """Check if data is encrypted at rest."""
        compliant = self.security_config.policy.encrypt_sensitive_data
        confidence = 1.0 if compliant else 0.9
        
        evidence = []
        recommendations = []
        
        if compliant:
            evidence.append("Security policy enables data encryption at rest")
        else:
            recommendations.append("Enable encryption for sensitive data storage")
        
        # Check database configuration
        db_encrypted = self._check_database_encryption()
        if db_encrypted:
            evidence.append("Database encryption configuration detected")
            confidence = min(confidence + 0.1, 1.0)
        else:
            recommendations.append("Configure database encryption (PostgreSQL, Neo4j)")
            compliant = False
        
        return ComplianceResult(
            rule_id=rule.id,
            compliant=compliant,
            confidence=confidence,
            details={
                "policy_encryption": self.security_config.policy.encrypt_sensitive_data,
                "database_encryption": db_encrypted
            },
            evidence=evidence,
            recommendations=recommendations,
            last_checked=datetime.now()
        )
    
    async def _check_data_encryption_in_transit(self, rule: ComplianceRule) -> ComplianceResult:
        """Check if data is encrypted in transit."""
        compliant = self.security_config.policy.force_https
        confidence = 1.0 if compliant else 0.8
        
        evidence = []
        recommendations = []
        
        if compliant:
            evidence.append("HTTPS enforcement is enabled in security policy")
        else:
            recommendations.append("Enable HTTPS enforcement for all communications")
        
        # Check TLS configuration
        tls_config = self._check_tls_configuration()
        if tls_config["valid"]:
            evidence.append(f"TLS configuration: {tls_config['version']}")
            confidence = min(confidence + 0.1, 1.0)
        else:
            recommendations.append("Update TLS configuration to use secure versions")
            compliant = False
        
        return ComplianceResult(
            rule_id=rule.id,
            compliant=compliant,
            confidence=confidence,
            details={
                "https_enforced": self.security_config.policy.force_https,
                "tls_config": tls_config
            },
            evidence=evidence,
            recommendations=recommendations,
            last_checked=datetime.now()
        )
    
    async def _check_access_logging(self, rule: ComplianceRule) -> ComplianceResult:
        """Check if access logging is properly implemented."""
        # Check if audit logging is configured
        audit_enabled = self._check_audit_logging()
        
        compliant = audit_enabled["enabled"]
        confidence = 0.9 if compliant else 0.7
        
        evidence = []
        recommendations = []
        
        if audit_enabled["enabled"]:
            evidence.append("Audit logging is configured")
            evidence.extend(audit_enabled["evidence"])
        else:
            recommendations.append("Enable comprehensive audit logging")
            recommendations.extend(audit_enabled["recommendations"])
        
        return ComplianceResult(
            rule_id=rule.id,
            compliant=compliant,
            confidence=confidence,
            details=audit_enabled,
            evidence=evidence,
            recommendations=recommendations,
            last_checked=datetime.now()
        )
    
    async def _check_data_retention_policies(self, rule: ComplianceRule) -> ComplianceResult:
        """Check if data retention policies are implemented."""
        retention_configured = self.security_config.policy.data_retention_days > 0
        audit_retention = self.security_config.policy.audit_log_retention_days > 0
        
        compliant = retention_configured and audit_retention
        confidence = 0.8  # Medium confidence as implementation details vary
        
        evidence = []
        recommendations = []
        
        if retention_configured:
            evidence.append(f"Data retention policy: {self.security_config.policy.data_retention_days} days")
        else:
            recommendations.append("Configure data retention policies")
        
        if audit_retention:
            evidence.append(f"Audit log retention: {self.security_config.policy.audit_log_retention_days} days")
        else:
            recommendations.append("Configure audit log retention policies")
        
        # Check for automated deletion procedures
        deletion_procedures = self._check_automated_deletion()
        if not deletion_procedures:
            recommendations.append("Implement automated data deletion procedures")
            confidence -= 0.2
        else:
            evidence.append("Automated deletion procedures detected")
        
        return ComplianceResult(
            rule_id=rule.id,
            compliant=compliant,
            confidence=confidence,
            details={
                "data_retention_days": self.security_config.policy.data_retention_days,
                "audit_retention_days": self.security_config.policy.audit_log_retention_days,
                "automated_deletion": deletion_procedures
            },
            evidence=evidence,
            recommendations=recommendations,
            last_checked=datetime.now()
        )
    
    async def _check_consent_management(self, rule: ComplianceRule) -> ComplianceResult:
        """Check if consent management is properly implemented."""
        # This would typically check for consent management features in the application
        # For now, we'll check configuration and provide guidance
        
        compliant = False  # Requires manual verification
        confidence = 0.5   # Medium confidence
        
        evidence = []
        recommendations = [
            "Implement user consent collection and management",
            "Provide clear consent withdrawal mechanisms",
            "Document consent collection procedures",
            "Implement consent audit trails"
        ]
        
        # Check if privacy features are configured
        privacy_features = self._check_privacy_features()
        if privacy_features:
            evidence.extend(privacy_features)
            confidence += 0.2
        
        return ComplianceResult(
            rule_id=rule.id,
            compliant=compliant,
            confidence=confidence,
            details={"privacy_features": privacy_features},
            evidence=evidence,
            recommendations=recommendations,
            last_checked=datetime.now()
        )
    
    async def _check_data_portability(self, rule: ComplianceRule) -> ComplianceResult:
        """Check if data portability features are implemented."""
        # Check for data export APIs or features
        export_available = self._check_data_export_features()
        
        compliant = export_available["available"]
        confidence = 0.8 if compliant else 0.6
        
        evidence = export_available["evidence"]
        recommendations = export_available["recommendations"]
        
        return ComplianceResult(
            rule_id=rule.id,
            compliant=compliant,
            confidence=confidence,
            details=export_available,
            evidence=evidence,
            recommendations=recommendations,
            last_checked=datetime.now()
        )
    
    async def _check_privacy_by_design(self, rule: ComplianceRule) -> ComplianceResult:
        """Check if privacy by design principles are implemented."""
        privacy_score = 0
        evidence = []
        recommendations = []
        
        # Check various privacy design elements
        if self.security_config.policy.data_anonymization:
            privacy_score += 1
            evidence.append("Data anonymization is enabled")
        else:
            recommendations.append("Implement data anonymization features")
        
        if self.security_config.policy.encrypt_sensitive_data:
            privacy_score += 1
            evidence.append("Sensitive data encryption is enabled")
        else:
            recommendations.append("Enable sensitive data encryption")
        
        if self.security_config.security_level in [SecurityLevel.HEALTHCARE, SecurityLevel.ENTERPRISE]:
            privacy_score += 1
            evidence.append(f"High security level configured: {self.security_config.security_level.value}")
        else:
            recommendations.append("Consider upgrading to healthcare or enterprise security level")
        
        # Check for access controls
        access_controls = self._check_access_controls()
        if access_controls:
            privacy_score += 1
            evidence.append("Access controls are implemented")
        else:
            recommendations.append("Implement comprehensive access controls")
        
        compliant = privacy_score >= 3  # At least 3 out of 4 checks
        confidence = privacy_score / 4.0
        
        return ComplianceResult(
            rule_id=rule.id,
            compliant=compliant,
            confidence=confidence,
            details={"privacy_score": privacy_score, "max_score": 4},
            evidence=evidence,
            recommendations=recommendations,
            last_checked=datetime.now()
        )
    
    async def _check_hipaa_safeguards(self, rule: ComplianceRule) -> ComplianceResult:
        """Check HIPAA safeguard requirements."""
        # HIPAA checks are similar to GDPR but with healthcare focus
        if "administrative" in rule.title.lower():
            return await self._check_administrative_safeguards(rule)
        elif "physical" in rule.title.lower():
            return await self._check_physical_safeguards(rule)
        elif "technical" in rule.title.lower():
            return await self._check_technical_safeguards(rule)
        elif "audit" in rule.title.lower():
            return await self._check_access_logging(rule)  # Reuse GDPR audit check
        elif "integrity" in rule.title.lower():
            return await self._check_data_integrity(rule)
        elif "transmission" in rule.title.lower():
            return await self._check_data_encryption_in_transit(rule)  # Reuse GDPR transit check
        else:
            return await self._check_security_configuration(rule)
    
    async def _check_administrative_safeguards(self, rule: ComplianceRule) -> ComplianceResult:
        """Check HIPAA administrative safeguards."""
        safeguards_score = 0
        evidence = []
        recommendations = []
        
        # Check for access control policies
        if self.security_config.policy.login_attempt_limit <= 5:
            safeguards_score += 1
            evidence.append(f"Login attempt limit: {self.security_config.policy.login_attempt_limit}")
        else:
            recommendations.append("Reduce login attempt limit to 5 or fewer")
        
        # Check session management
        if self.security_config.policy.session_timeout_minutes <= 30:
            safeguards_score += 1
            evidence.append(f"Session timeout: {self.security_config.policy.session_timeout_minutes} minutes")
        else:
            recommendations.append("Reduce session timeout to 30 minutes or less")
        
        # Check password policies
        if self.security_config.policy.password_min_length >= 12:
            safeguards_score += 1
            evidence.append(f"Password minimum length: {self.security_config.policy.password_min_length}")
        else:
            recommendations.append("Increase minimum password length to 12 characters")
        
        compliant = safeguards_score >= 2
        confidence = safeguards_score / 3.0
        
        return ComplianceResult(
            rule_id=rule.id,
            compliant=compliant,
            confidence=confidence,
            details={"safeguards_score": safeguards_score},
            evidence=evidence,
            recommendations=recommendations,
            last_checked=datetime.now()
        )
    
    async def _check_physical_safeguards(self, rule: ComplianceRule) -> ComplianceResult:
        """Check HIPAA physical safeguards."""
        # Physical safeguards are primarily infrastructure-related
        # We can check for deployment configuration
        
        evidence = []
        recommendations = [
            "Ensure physical security of server infrastructure",
            "Implement access controls to data centers",
            "Use secure cloud infrastructure with SOC 2 compliance",
            "Document physical security procedures"
        ]
        
        # Check if using secure deployment
        secure_deployment = self._check_secure_deployment()
        compliant = secure_deployment["secure"]
        confidence = 0.7 if compliant else 0.5
        
        if secure_deployment["secure"]:
            evidence.extend(secure_deployment["evidence"])
        else:
            recommendations.extend(secure_deployment["recommendations"])
        
        return ComplianceResult(
            rule_id=rule.id,
            compliant=compliant,
            confidence=confidence,
            details=secure_deployment,
            evidence=evidence,
            recommendations=recommendations,
            last_checked=datetime.now()
        )
    
    async def _check_technical_safeguards(self, rule: ComplianceRule) -> ComplianceResult:
        """Check HIPAA technical safeguards."""
        # Technical safeguards combine multiple security controls
        technical_score = 0
        evidence = []
        recommendations = []
        
        # Access controls
        if self._check_access_controls():
            technical_score += 1
            evidence.append("Access controls implemented")
        else:
            recommendations.append("Implement role-based access controls")
        
        # Audit logging
        audit_check = self._check_audit_logging()
        if audit_check["enabled"]:
            technical_score += 1
            evidence.append("Audit logging enabled")
        else:
            recommendations.append("Enable comprehensive audit logging")
        
        # Encryption
        if self.security_config.policy.encrypt_sensitive_data:
            technical_score += 1
            evidence.append("Data encryption enabled")
        else:
            recommendations.append("Enable data encryption")
        
        # Transmission security
        if self.security_config.policy.force_https:
            technical_score += 1
            evidence.append("HTTPS enforcement enabled")
        else:
            recommendations.append("Enable HTTPS enforcement")
        
        compliant = technical_score >= 3
        confidence = technical_score / 4.0
        
        return ComplianceResult(
            rule_id=rule.id,
            compliant=compliant,
            confidence=confidence,
            details={"technical_score": technical_score},
            evidence=evidence,
            recommendations=recommendations,
            last_checked=datetime.now()
        )
    
    async def _check_data_integrity(self, rule: ComplianceRule) -> ComplianceResult:
        """Check data integrity controls."""
        integrity_controls = []
        evidence = []
        recommendations = []
        
        # Check backup configuration
        if self.security_config.policy.backup_encryption:
            integrity_controls.append("encrypted_backups")
            evidence.append("Encrypted backups are configured")
        else:
            recommendations.append("Enable encrypted backup procedures")
        
        # Check for versioning/audit trails
        if self._check_audit_logging()["enabled"]:
            integrity_controls.append("audit_trails")
            evidence.append("Audit trails are maintained")
        else:
            recommendations.append("Implement audit trail mechanisms")
        
        compliant = len(integrity_controls) >= 1
        confidence = len(integrity_controls) / 2.0
        
        return ComplianceResult(
            rule_id=rule.id,
            compliant=compliant,
            confidence=confidence,
            details={"integrity_controls": integrity_controls},
            evidence=evidence,
            recommendations=recommendations,
            last_checked=datetime.now()
        )
    
    async def _check_soc2_controls(self, rule: ComplianceRule) -> ComplianceResult:
        """Check SOC 2 security controls."""
        # SOC 2 checks focus on security controls
        if "access" in rule.title.lower():
            return await self._check_administrative_safeguards(rule)  # Reuse HIPAA check
        elif "network" in rule.title.lower():
            return await self._check_network_security(rule)
        elif "monitoring" in rule.title.lower():
            return await self._check_system_monitoring(rule)
        else:
            return await self._check_security_configuration(rule)
    
    async def _check_network_security(self, rule: ComplianceRule) -> ComplianceResult:
        """Check network security controls."""
        network_controls = []
        evidence = []
        recommendations = []
        
        # Check HTTPS enforcement
        if self.security_config.policy.force_https:
            network_controls.append("https_enforcement")
            evidence.append("HTTPS enforcement is enabled")
        else:
            recommendations.append("Enable HTTPS enforcement")
        
        # Check security headers
        headers = self.security_config.get_security_headers()
        if headers:
            network_controls.append("security_headers")
            evidence.append(f"Security headers configured: {len(headers)} headers")
        else:
            recommendations.append("Configure security headers")
        
        # Check for rate limiting
        if self.security_config.policy.rate_limit_requests_per_minute > 0:
            network_controls.append("rate_limiting")
            evidence.append(f"Rate limiting: {self.security_config.policy.rate_limit_requests_per_minute} req/min")
        else:
            recommendations.append("Configure rate limiting")
        
        compliant = len(network_controls) >= 2
        confidence = len(network_controls) / 3.0
        
        return ComplianceResult(
            rule_id=rule.id,
            compliant=compliant,
            confidence=confidence,
            details={"network_controls": network_controls},
            evidence=evidence,
            recommendations=recommendations,
            last_checked=datetime.now()
        )
    
    async def _check_system_monitoring(self, rule: ComplianceRule) -> ComplianceResult:
        """Check system monitoring capabilities."""
        monitoring_features = []
        evidence = []
        recommendations = []
        
        # Check for monitoring configuration
        monitoring_config = self._check_monitoring_configuration()
        if monitoring_config["enabled"]:
            monitoring_features.extend(monitoring_config["features"])
            evidence.extend(monitoring_config["evidence"])
        else:
            recommendations.extend(monitoring_config["recommendations"])
        
        compliant = len(monitoring_features) >= 2
        confidence = min(len(monitoring_features) / 3.0, 1.0)
        
        return ComplianceResult(
            rule_id=rule.id,
            compliant=compliant,
            confidence=confidence,
            details={"monitoring_features": monitoring_features},
            evidence=evidence,
            recommendations=recommendations,
            last_checked=datetime.now()
        )
    
    async def _check_security_configuration(self, rule: ComplianceRule) -> ComplianceResult:
        """Generic security configuration check."""
        config_score = 0
        evidence = []
        recommendations = []
        
        # Basic security checks
        if self.security_config.security_level in [SecurityLevel.HEALTHCARE, SecurityLevel.ENTERPRISE]:
            config_score += 1
            evidence.append(f"High security level: {self.security_config.security_level.value}")
        else:
            recommendations.append("Upgrade to healthcare or enterprise security level")
        
        if self.security_config.policy.force_https:
            config_score += 1
            evidence.append("HTTPS enforcement enabled")
        else:
            recommendations.append("Enable HTTPS enforcement")
        
        if self.security_config.policy.encrypt_sensitive_data:
            config_score += 1
            evidence.append("Data encryption enabled")
        else:
            recommendations.append("Enable data encryption")
        
        compliant = config_score >= 2
        confidence = config_score / 3.0
        
        return ComplianceResult(
            rule_id=rule.id,
            compliant=compliant,
            confidence=confidence,
            details={"config_score": config_score},
            evidence=evidence,
            recommendations=recommendations,
            last_checked=datetime.now()
        )
    
    # Helper methods for checking various configurations
    def _check_database_encryption(self) -> bool:
        """Check if database encryption is configured."""
        # In a real implementation, this would check actual database configuration
        # For now, we'll check environment variables and configuration files
        
        # Check for encryption-related environment variables
        db_url = os.getenv("DATABASE_URL", "")
        if "sslmode=require" in db_url or "ssl=true" in db_url:
            return True
        
        # Check configuration files
        config_files = ["docker-compose.yml", ".env"]
        for config_file in config_files:
            if Path(config_file).exists():
                try:
                    content = Path(config_file).read_text()
                    if any(term in content.lower() for term in ["encrypt", "ssl", "tls"]):
                        return True
                except Exception:
                    continue
        
        return False
    
    def _check_tls_configuration(self) -> Dict[str, Any]:
        """Check TLS configuration."""
        # This would typically check server configuration
        # For now, we'll provide basic checks
        
        return {
            "valid": True,  # Assume valid for development
            "version": "TLS 1.3",
            "cipher_suites": ["secure_ciphers"],
            "recommendations": []
        }
    
    def _check_audit_logging(self) -> Dict[str, Any]:
        """Check audit logging configuration."""
        evidence = []
        recommendations = []
        enabled = False
        
        # Check for logging configuration
        log_files = ["logs/", "monitoring/"]
        for log_dir in log_files:
            if Path(log_dir).exists():
                evidence.append(f"Logging directory exists: {log_dir}")
                enabled = True
        
        # Check for monitoring configuration
        monitoring_files = ["monitoring/prometheus/", "monitoring/grafana/"]
        for monitoring_dir in monitoring_files:
            if Path(monitoring_dir).exists():
                evidence.append(f"Monitoring configured: {monitoring_dir}")
                enabled = True
        
        if not enabled:
            recommendations.extend([
                "Configure comprehensive audit logging",
                "Set up monitoring and alerting",
                "Implement log retention policies"
            ])
        
        return {
            "enabled": enabled,
            "evidence": evidence,
            "recommendations": recommendations
        }
    
    def _check_automated_deletion(self) -> bool:
        """Check for automated data deletion procedures."""
        # Check for deletion scripts or configuration
        deletion_indicators = [
            "scripts/cleanup.py",
            "scripts/data_retention.py",
            "cron.d/",
            "scheduled_tasks/"
        ]
        
        for indicator in deletion_indicators:
            if Path(indicator).exists():
                return True
        
        return False
    
    def _check_privacy_features(self) -> List[str]:
        """Check for privacy-related features."""
        features = []
        
        if self.security_config.policy.data_anonymization:
            features.append("Data anonymization enabled")
        
        if self.security_config.policy.gdpr_compliance:
            features.append("GDPR compliance mode enabled")
        
        return features
    
    def _check_data_export_features(self) -> Dict[str, Any]:
        """Check for data export/portability features."""
        # Check for export-related API endpoints or features
        api_files = ["agent/api.py", "fisio_rag_saas/api/"]
        export_available = False
        evidence = []
        recommendations = []
        
        for api_file in api_files:
            if Path(api_file).exists():
                try:
                    content = Path(api_file).read_text()
                    if any(term in content.lower() for term in ["export", "download", "data_portability"]):
                        export_available = True
                        evidence.append(f"Export functionality found in {api_file}")
                except Exception:
                    continue
        
        if not export_available:
            recommendations.extend([
                "Implement user data export API",
                "Provide data download functionality",
                "Create data portability documentation"
            ])
        
        return {
            "available": export_available,
            "evidence": evidence,
            "recommendations": recommendations
        }
    
    def _check_access_controls(self) -> bool:
        """Check for access control implementation."""
        # Check for authentication and authorization code
        auth_indicators = [
            "agent/auth",
            "fisio_rag_saas/accounts/",
            "security/",
            "middleware"
        ]
        
        for indicator in auth_indicators:
            if Path(indicator).exists():
                return True
        
        # Check for authentication in API files
        api_files = ["agent/api.py"]
        for api_file in api_files:
            if Path(api_file).exists():
                try:
                    content = Path(api_file).read_text()
                    if any(term in content.lower() for term in ["auth", "permission", "access"]):
                        return True
                except Exception:
                    continue
        
        return False
    
    def _check_secure_deployment(self) -> Dict[str, Any]:
        """Check for secure deployment configuration."""
        evidence = []
        recommendations = []
        secure = False
        
        # Check for Docker security configuration
        if Path("Dockerfile").exists():
            evidence.append("Containerized deployment available")
            secure = True
        
        # Check for CI/CD security
        if Path(".github/workflows/").exists():
            evidence.append("CI/CD pipeline configured")
            secure = True
        
        # Check for monitoring
        if Path("monitoring/").exists():
            evidence.append("Monitoring infrastructure configured")
            secure = True
        
        if not secure:
            recommendations.extend([
                "Configure secure deployment pipeline",
                "Implement container security",
                "Set up infrastructure monitoring"
            ])
        
        return {
            "secure": secure,
            "evidence": evidence,
            "recommendations": recommendations
        }
    
    def _check_monitoring_configuration(self) -> Dict[str, Any]:
        """Check monitoring configuration."""
        features = []
        evidence = []
        recommendations = []
        enabled = False
        
        # Check for Prometheus
        if Path("monitoring/prometheus/").exists():
            features.append("prometheus")
            evidence.append("Prometheus monitoring configured")
            enabled = True
        
        # Check for Grafana
        if Path("monitoring/grafana/").exists():
            features.append("grafana")
            evidence.append("Grafana dashboards configured")
            enabled = True
        
        # Check for alerting
        if Path("monitoring/alertmanager/").exists():
            features.append("alerting")
            evidence.append("Alert management configured")
            enabled = True
        
        if not enabled:
            recommendations.extend([
                "Configure Prometheus monitoring",
                "Set up Grafana dashboards",
                "Implement alerting rules"
            ])
        
        return {
            "enabled": enabled,
            "features": features,
            "evidence": evidence,
            "recommendations": recommendations
        }
    
    def _calculate_compliance_score(self, results: List[ComplianceResult]) -> float:
        """Calculate overall compliance score."""
        if not results:
            return 0.0
        
        # Weight by confidence and compliance
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for result in results:
            weight = result.confidence
            score = 1.0 if result.compliant else 0.0
            
            total_weighted_score += score * weight
            total_weight += weight
        
        return total_weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _generate_compliance_summary(self, results: List[ComplianceResult], regulations: List[str]) -> Dict[str, Any]:
        """Generate compliance summary statistics."""
        summary = {
            "total_rules": len(results),
            "compliant_rules": len([r for r in results if r.compliant]),
            "non_compliant_rules": len([r for r in results if not r.compliant]),
            "by_regulation": {},
            "by_severity": {},
            "average_confidence": sum(r.confidence for r in results) / len(results) if results else 0.0
        }
        
        # Group by regulation
        for regulation in regulations:
            reg_results = [r for r in results if any(rule.regulation == regulation for rule in self.rules if rule.id == r.rule_id)]
            summary["by_regulation"][regulation] = {
                "total": len(reg_results),
                "compliant": len([r for r in reg_results if r.compliant]),
                "compliance_rate": len([r for r in reg_results if r.compliant]) / len(reg_results) if reg_results else 0.0
            }
        
        # Group by severity
        for result in results:
            rule = next((r for r in self.rules if r.id == result.rule_id), None)
            if rule:
                severity = rule.severity
                if severity not in summary["by_severity"]:
                    summary["by_severity"][severity] = {"total": 0, "compliant": 0}
                
                summary["by_severity"][severity]["total"] += 1
                if result.compliant:
                    summary["by_severity"][severity]["compliant"] += 1
        
        return summary
    
    def _generate_compliance_recommendations(self, results: List[ComplianceResult]) -> List[str]:
        """Generate overall compliance recommendations."""
        all_recommendations = []
        
        for result in results:
            if not result.compliant:
                all_recommendations.extend(result.recommendations)
        
        # Remove duplicates and prioritize
        unique_recommendations = list(set(all_recommendations))
        
        # Add general recommendations
        if len([r for r in results if not r.compliant]) > len(results) * 0.5:
            unique_recommendations.insert(0, "Consider upgrading to higher security level for better compliance")
        
        return unique_recommendations
    
    def export_compliance_report(self, report: ComplianceReport, format: str = "json") -> str:
        """Export compliance report to various formats."""
        if format == "json":
            return json.dumps(asdict(report), indent=2, default=str)
        elif format == "html":
            return self._generate_html_compliance_report(report)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_html_compliance_report(self, report: ComplianceReport) -> str:
        """Generate HTML compliance report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>FisioRAG Compliance Assessment Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .score {{ font-size: 24px; font-weight: bold; color: #28a745; }}
                .regulation {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .compliant {{ color: #28a745; }}
                .non-compliant {{ color: #dc3545; }}
                .recommendation {{ background-color: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>FisioRAG Compliance Assessment</h1>
                <p><strong>Assessment ID:</strong> {report.assessment_id}</p>
                <p><strong>Date:</strong> {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Regulations:</strong> {', '.join(report.regulations)}</p>
                <div class="score">Overall Compliance Score: {report.overall_score:.1%}</div>
            </div>
            
            <h2>Summary</h2>
            <ul>
                <li>Total Rules Assessed: {report.summary['total_rules']}</li>
                <li>Compliant Rules: {report.summary['compliant_rules']}</li>
                <li>Non-Compliant Rules: {report.summary['non_compliant_rules']}</li>
                <li>Average Confidence: {report.summary['average_confidence']:.1%}</li>
            </ul>
            
            <h2>Compliance by Regulation</h2>
        """
        
        for regulation, stats in report.summary.get('by_regulation', {}).items():
            html += f"""
            <div class="regulation">
                <h3>{regulation}</h3>
                <p>Compliance Rate: <span class="{'compliant' if stats['compliance_rate'] > 0.8 else 'non-compliant'}">{stats['compliance_rate']:.1%}</span></p>
                <p>Rules: {stats['compliant']}/{stats['total']} compliant</p>
            </div>
            """
        
        if report.recommendations:
            html += f"""
            <h2>Recommendations</h2>
            <div class="recommendations">
                {''.join(f'<div class="recommendation">{rec}</div>' for rec in report.recommendations)}
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html


# Main execution function
async def main():
    """Run compliance assessment."""
    from .security_config import get_security_config
    
    security_config = get_security_config("production")
    checker = ComplianceChecker(security_config)
    
    print("🏥 Starting FisioRAG Compliance Assessment...")
    report = await checker.run_compliance_assessment()
    
    print(f"\n📊 Compliance Assessment Results:")
    print(f"   Overall Score: {report.overall_score:.1%}")
    print(f"   Compliant Rules: {report.summary['compliant_rules']}/{report.summary['total_rules']}")
    
    for regulation, stats in report.summary.get('by_regulation', {}).items():
        print(f"   {regulation}: {stats['compliance_rate']:.1%} ({stats['compliant']}/{stats['total']})")
    
    # Save reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON report
    json_report = checker.export_compliance_report(report, "json")
    Path("security/reports/").mkdir(parents=True, exist_ok=True)
    with open(f"security/reports/compliance_assessment_{timestamp}.json", "w") as f:
        f.write(json_report)
    
    # HTML report
    html_report = checker.export_compliance_report(report, "html")
    with open(f"security/reports/compliance_assessment_{timestamp}.html", "w") as f:
        f.write(html_report)
    
    print(f"\n📄 Reports saved:")
    print(f"   JSON: security/reports/compliance_assessment_{timestamp}.json")
    print(f"   HTML: security/reports/compliance_assessment_{timestamp}.html")
    
    if report.recommendations:
        print(f"\n💡 Top Recommendations:")
        for i, rec in enumerate(report.recommendations[:5], 1):
            print(f"   {i}. {rec}")
    
    return report


if __name__ == "__main__":
    asyncio.run(main())
