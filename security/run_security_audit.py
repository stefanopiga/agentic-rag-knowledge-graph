#!/usr/bin/env python3
"""
FisioRAG Security Audit Runner.
Comprehensive security assessment and hardening validation.
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import argparse

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from security.security_config import SecurityHardening, SecurityLevel, get_security_config
from security.vulnerability_scanner import VulnerabilityScanner
from security.compliance_checker import ComplianceChecker


def setup_logging(verbose: bool = False) -> Path:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create logs directory
    logs_dir = Path("security/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup file and console logging
    log_filename = logs_dir / f"security_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return log_filename


def print_banner():
    """Print security audit banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║              FisioRAG Security Audit Suite                  ║
║                                                              ║
║  Enterprise-grade security assessment for healthcare AI     ║
║  • Vulnerability Scanning & Threat Detection                ║
║  • GDPR, HIPAA, SOC2 Compliance Validation                 ║
║  • Security Configuration Assessment                        ║
║  • Automated Remediation Recommendations                    ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


async def run_vulnerability_scan(output_dir: Path, verbose: bool = False) -> Dict[str, Any]:
    """Run comprehensive vulnerability scanning."""
    print("\n🔍 Running Vulnerability Scan...")
    print("=" * 60)
    
    scanner = VulnerabilityScanner()
    scan_result = await scanner.run_comprehensive_scan()
    
    # Print summary
    print(f"✅ Scan completed in {scan_result.duration_seconds:.1f} seconds")
    print(f"📊 Total vulnerabilities found: {scan_result.summary['total']}")
    
    severity_colors = {
        'critical': '🚨',
        'high': '🔴', 
        'medium': '🟡',
        'low': '🟢'
    }
    
    for severity in ['critical', 'high', 'medium', 'low']:
        count = scan_result.summary.get(severity, 0)
        if count > 0:
            print(f"   {severity_colors[severity]} {severity.title()}: {count}")
    
    # Show top vulnerabilities
    critical_high = [v for v in scan_result.vulnerabilities if v.severity in ['critical', 'high']]
    if critical_high:
        print(f"\n⚠️  Critical/High Severity Issues:")
        for vuln in critical_high[:5]:  # Show first 5
            print(f"   • {vuln.title} ({vuln.severity})")
            if vuln.file_path:
                print(f"     📁 {vuln.file_path}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON report
    json_report = scanner.export_results(scan_result, "json")
    json_path = output_dir / f"vulnerability_scan_{timestamp}.json"
    with open(json_path, "w") as f:
        f.write(json_report)
    
    # HTML report
    html_report = scanner.export_results(scan_result, "html")
    html_path = output_dir / f"vulnerability_scan_{timestamp}.html"
    with open(html_path, "w") as f:
        f.write(html_report)
    
    print(f"\n📄 Vulnerability reports saved:")
    print(f"   JSON: {json_path}")
    print(f"   HTML: {html_path}")
    
    return {
        "scan_result": scan_result,
        "json_path": str(json_path),
        "html_path": str(html_path)
    }


async def run_compliance_assessment(security_config: SecurityHardening, output_dir: Path, 
                                  regulations: List[str] = None) -> Dict[str, Any]:
    """Run compliance assessment."""
    print("\n🏥 Running Compliance Assessment...")
    print("=" * 60)
    
    if regulations is None:
        regulations = ["GDPR", "HIPAA", "SOC2"]
    
    print(f"📋 Assessing compliance with: {', '.join(regulations)}")
    
    checker = ComplianceChecker(security_config)
    report = await checker.run_compliance_assessment(regulations)
    
    # Print summary
    print(f"✅ Assessment completed")
    print(f"📊 Overall compliance score: {report.overall_score:.1%}")
    print(f"📋 Rules assessed: {report.summary['compliant_rules']}/{report.summary['total_rules']} compliant")
    
    # Show compliance by regulation
    for regulation, stats in report.summary.get('by_regulation', {}).items():
        status_emoji = "✅" if stats['compliance_rate'] > 0.8 else "⚠️" if stats['compliance_rate'] > 0.6 else "❌"
        print(f"   {status_emoji} {regulation}: {stats['compliance_rate']:.1%} ({stats['compliant']}/{stats['total']})")
    
    # Show critical recommendations
    if report.recommendations:
        print(f"\n💡 Key Recommendations:")
        for i, rec in enumerate(report.recommendations[:5], 1):
            print(f"   {i}. {rec}")
    
    # Save reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON report
    json_report = checker.export_compliance_report(report, "json")
    json_path = output_dir / f"compliance_assessment_{timestamp}.json"
    with open(json_path, "w") as f:
        f.write(json_report)
    
    # HTML report
    html_report = checker.export_compliance_report(report, "html") 
    html_path = output_dir / f"compliance_assessment_{timestamp}.html"
    with open(html_path, "w") as f:
        f.write(html_report)
    
    print(f"\n📄 Compliance reports saved:")
    print(f"   JSON: {json_path}")
    print(f"   HTML: {html_path}")
    
    return {
        "report": report,
        "json_path": str(json_path),
        "html_path": str(html_path)
    }


async def run_security_configuration_check(security_config: SecurityHardening, 
                                         output_dir: Path) -> Dict[str, Any]:
    """Run security configuration assessment."""
    print("\n🔧 Running Security Configuration Check...")
    print("=" * 60)
    
    # Generate security report
    config_report = security_config.generate_security_report()
    
    # Print summary
    print(f"🔒 Security Level: {config_report['security_level']}")
    
    # Password policies
    pwd_policy = config_report['policy_summary']['password_requirements']
    print(f"🔑 Password Policy:")
    print(f"   • Min length: {pwd_policy['min_length']} characters")
    print(f"   • Complexity required: {'✅' if pwd_policy['complexity_required'] else '❌'}")
    print(f"   • Max age: {pwd_policy['max_age_days']} days")
    
    # Session security
    session_policy = config_report['policy_summary']['session_security']
    print(f"⏱️  Session Security:")
    print(f"   • Timeout: {session_policy['timeout_minutes']} minutes")
    print(f"   • Secure cookies: {'✅' if session_policy['secure_cookies'] else '❌'}")
    
    # API protection
    api_policy = config_report['policy_summary']['api_protection']
    print(f"🛡️  API Protection:")
    print(f"   • Rate limit: {api_policy['rate_limit_rpm']} requests/min")
    print(f"   • CORS configured: {'✅' if api_policy['cors_configured'] else '❌'}")
    
    # Compliance status
    compliance = config_report['policy_summary']['compliance']
    print(f"📋 Compliance Configuration:")
    print(f"   • GDPR: {'✅' if compliance['gdpr_enabled'] else '❌'}")
    print(f"   • HIPAA: {'✅' if compliance['hipaa_enabled'] else '❌'}")
    print(f"   • Data encryption: {'✅' if compliance['data_encryption'] else '❌'}")
    
    # Recommendations
    if config_report['recommendations']:
        print(f"\n💡 Configuration Recommendations:")
        for i, rec in enumerate(config_report['recommendations'], 1):
            print(f"   {i}. {rec}")
    
    # Save configuration report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    config_path = output_dir / f"security_config_{timestamp}.json"
    
    with open(config_path, "w") as f:
        json.dump(config_report, f, indent=2, default=str)
    
    print(f"\n📄 Configuration report saved: {config_path}")
    
    return {
        "config_report": config_report,
        "config_path": str(config_path)
    }


async def run_comprehensive_audit(environment: str = "production", 
                                regulations: List[str] = None,
                                verbose: bool = False) -> Dict[str, Any]:
    """Run comprehensive security audit."""
    print_banner()
    
    # Setup
    log_file = setup_logging(verbose)
    print(f"🔗 Environment: {environment}")
    print(f"📝 Log file: {log_file}")
    print(f"⏰ Audit started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create output directory
    output_dir = Path("security/reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get security configuration
    security_config = get_security_config(environment)
    
    try:
        # Run all security assessments
        results = {}
        
        # 1. Vulnerability scanning
        vuln_results = await run_vulnerability_scan(output_dir, verbose)
        results["vulnerability_scan"] = vuln_results
        
        # 2. Compliance assessment
        compliance_results = await run_compliance_assessment(security_config, output_dir, regulations)
        results["compliance_assessment"] = compliance_results
        
        # 3. Security configuration check
        config_results = await run_security_configuration_check(security_config, output_dir)
        results["security_configuration"] = config_results
        
        # Generate executive summary
        executive_summary = generate_executive_summary(results)
        
        # Save executive summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_path = output_dir / f"executive_summary_{timestamp}.json"
        
        with open(summary_path, "w") as f:
            json.dump(executive_summary, f, indent=2, default=str)
        
        # Print final summary
        print_final_summary(executive_summary)
        
        print(f"\n📊 Executive summary saved: {summary_path}")
        print(f"📁 All reports available in: {output_dir}")
        
        return {
            "executive_summary": executive_summary,
            "summary_path": str(summary_path),
            "output_directory": str(output_dir),
            "results": results
        }
        
    except Exception as e:
        logging.error(f"Security audit failed: {e}", exc_info=True)
        print(f"\n❌ Audit failed: {e}")
        return {"error": str(e)}


def generate_executive_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate executive summary of security audit."""
    summary = {
        "audit_metadata": {
            "timestamp": datetime.now().isoformat(),
            "audit_type": "comprehensive_security_assessment",
            "scope": ["vulnerability_scanning", "compliance_assessment", "configuration_review"]
        },
        "overall_security_posture": "unknown",
        "risk_level": "unknown",
        "key_findings": {},
        "critical_issues": [],
        "recommendations": [],
        "compliance_status": {},
        "next_steps": []
    }
    
    # Analyze vulnerability scan results
    if "vulnerability_scan" in results:
        vuln_result = results["vulnerability_scan"]["scan_result"]
        
        critical_high = vuln_result.summary.get('critical', 0) + vuln_result.summary.get('high', 0)
        
        summary["key_findings"]["vulnerabilities"] = {
            "total": vuln_result.summary['total'],
            "critical_high": critical_high,
            "by_category": vuln_result.summary.get('by_category', {})
        }
        
        # Add critical vulnerabilities to issues
        for vuln in vuln_result.vulnerabilities:
            if vuln.severity in ['critical', 'high']:
                summary["critical_issues"].append({
                    "type": "vulnerability",
                    "severity": vuln.severity,
                    "title": vuln.title,
                    "category": vuln.category
                })
    
    # Analyze compliance results
    if "compliance_assessment" in results:
        compliance_report = results["compliance_assessment"]["report"]
        
        summary["key_findings"]["compliance"] = {
            "overall_score": compliance_report.overall_score,
            "by_regulation": compliance_report.summary.get('by_regulation', {})
        }
        
        # Set compliance status
        for regulation, stats in compliance_report.summary.get('by_regulation', {}).items():
            summary["compliance_status"][regulation] = {
                "compliant": stats['compliance_rate'] > 0.8,
                "score": stats['compliance_rate'],
                "issues": stats['total'] - stats['compliant']
            }
    
    # Analyze configuration results
    if "security_configuration" in results:
        config_report = results["security_configuration"]["config_report"]
        
        summary["key_findings"]["configuration"] = {
            "security_level": config_report['security_level'],
            "recommendations_count": len(config_report.get('recommendations', []))
        }
    
    # Determine overall security posture
    vulnerability_score = 1.0
    if "vulnerability_scan" in results:
        vuln_result = results["vulnerability_scan"]["scan_result"]
        critical_high = vuln_result.summary.get('critical', 0) + vuln_result.summary.get('high', 0)
        if critical_high > 10:
            vulnerability_score = 0.3
        elif critical_high > 5:
            vulnerability_score = 0.6
        elif critical_high > 0:
            vulnerability_score = 0.8
    
    compliance_score = 0.7  # Default
    if "compliance_assessment" in results:
        compliance_score = results["compliance_assessment"]["report"].overall_score
    
    # Overall score (weighted average)
    overall_score = (vulnerability_score * 0.4) + (compliance_score * 0.6)
    
    if overall_score >= 0.9:
        summary["overall_security_posture"] = "excellent"
        summary["risk_level"] = "low"
    elif overall_score >= 0.8:
        summary["overall_security_posture"] = "good"
        summary["risk_level"] = "low"
    elif overall_score >= 0.7:
        summary["overall_security_posture"] = "acceptable"
        summary["risk_level"] = "medium"
    elif overall_score >= 0.6:
        summary["overall_security_posture"] = "needs_improvement"
        summary["risk_level"] = "medium"
    else:
        summary["overall_security_posture"] = "poor"
        summary["risk_level"] = "high"
    
    # Generate recommendations
    summary["recommendations"] = []
    
    if len(summary["critical_issues"]) > 0:
        summary["recommendations"].append("Address all critical and high severity vulnerabilities immediately")
    
    if compliance_score < 0.8:
        summary["recommendations"].append("Improve compliance posture to meet regulatory requirements")
    
    if vulnerability_score < 0.8:
        summary["recommendations"].append("Implement additional security controls and monitoring")
    
    # Next steps
    summary["next_steps"] = [
        "Review and prioritize security recommendations",
        "Implement remediation plan for critical issues",
        "Schedule regular security assessments (monthly)",
        "Update security policies and procedures",
        "Conduct security training for development team"
    ]
    
    return summary


def print_final_summary(summary: Dict[str, Any]):
    """Print final audit summary."""
    print("\n" + "="*80)
    print("🎯 EXECUTIVE SUMMARY")
    print("="*80)
    
    # Overall posture
    posture = summary["overall_security_posture"]
    risk = summary["risk_level"]
    
    posture_colors = {
        "excellent": "🟢",
        "good": "🟢", 
        "acceptable": "🟡",
        "needs_improvement": "🟠",
        "poor": "🔴"
    }
    
    risk_colors = {
        "low": "🟢",
        "medium": "🟡", 
        "high": "🔴"
    }
    
    print(f"🛡️  Overall Security Posture: {posture_colors.get(posture, '⚪')} {posture.replace('_', ' ').title()}")
    print(f"⚠️  Risk Level: {risk_colors.get(risk, '⚪')} {risk.title()}")
    
    # Key findings
    if "vulnerabilities" in summary["key_findings"]:
        vuln_findings = summary["key_findings"]["vulnerabilities"]
        print(f"\n🔍 Vulnerability Assessment:")
        print(f"   Total vulnerabilities: {vuln_findings['total']}")
        print(f"   Critical/High severity: {vuln_findings['critical_high']}")
    
    if "compliance" in summary["key_findings"]:
        comp_findings = summary["key_findings"]["compliance"]
        print(f"\n📋 Compliance Assessment:")
        print(f"   Overall score: {comp_findings['overall_score']:.1%}")
        
        for regulation, stats in comp_findings['by_regulation'].items():
            status = "✅" if stats['compliance_rate'] > 0.8 else "⚠️" if stats['compliance_rate'] > 0.6 else "❌"
            print(f"   {status} {regulation}: {stats['compliance_rate']:.1%}")
    
    # Critical issues
    if summary["critical_issues"]:
        print(f"\n🚨 Critical Issues ({len(summary['critical_issues'])}):")
        for issue in summary["critical_issues"][:5]:  # Show first 5
            print(f"   • {issue['title']} ({issue['severity']})")
    
    # Top recommendations
    if summary["recommendations"]:
        print(f"\n💡 Priority Recommendations:")
        for i, rec in enumerate(summary["recommendations"][:3], 1):
            print(f"   {i}. {rec}")
    
    print("\n" + "="*80)


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="FisioRAG Security Audit Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python security/run_security_audit.py --comprehensive
  python security/run_security_audit.py --vulnerability-scan
  python security/run_security_audit.py --compliance --regulations GDPR HIPAA
  python security/run_security_audit.py --config-check --environment production
        """
    )
    
    # Test selection
    test_group = parser.add_mutually_exclusive_group(required=True)
    test_group.add_argument(
        "--comprehensive",
        action="store_true",
        help="Run complete security audit (all assessments)"
    )
    test_group.add_argument(
        "--vulnerability-scan",
        action="store_true", 
        help="Run vulnerability scanning only"
    )
    test_group.add_argument(
        "--compliance",
        action="store_true",
        help="Run compliance assessment only"
    )
    test_group.add_argument(
        "--config-check",
        action="store_true",
        help="Run security configuration check only"
    )
    
    # Options
    parser.add_argument(
        "--environment",
        choices=["development", "staging", "production"],
        default="production",
        help="Target environment for assessment"
    )
    parser.add_argument(
        "--regulations",
        nargs="+",
        choices=["GDPR", "HIPAA", "SOC2"],
        default=["GDPR", "HIPAA", "SOC2"],
        help="Regulations to assess compliance against"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Run selected assessment
    try:
        if args.comprehensive:
            result = asyncio.run(run_comprehensive_audit(
                environment=args.environment,
                regulations=args.regulations,
                verbose=args.verbose
            ))
        else:
            # Setup for individual assessments
            log_file = setup_logging(args.verbose)
            output_dir = Path("security/reports")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if args.vulnerability_scan:
                print_banner()
                result = asyncio.run(run_vulnerability_scan(output_dir, args.verbose))
            elif args.compliance:
                print_banner()
                security_config = get_security_config(args.environment)
                result = asyncio.run(run_compliance_assessment(
                    security_config, output_dir, args.regulations
                ))
            elif args.config_check:
                print_banner()
                security_config = get_security_config(args.environment)
                result = asyncio.run(run_security_configuration_check(
                    security_config, output_dir
                ))
        
        if "error" in result:
            print(f"\n❌ Assessment failed: {result['error']}")
            return 1
        
        print(f"\n✅ Security assessment completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️  Assessment interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Assessment failed: {e}")
        logging.error(f"Assessment execution failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
