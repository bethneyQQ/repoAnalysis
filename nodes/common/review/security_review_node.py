from engine import node
import re
from typing import List, Dict, Any

def security_review_node():
    """Security vulnerability detection node

    Checks for common security issues:
    - SQL injection
    - Hardcoded secrets
    - Command injection
    - Path traversal
    - Unsafe deserialization
    - Weak cryptography

    Parameters:
        - check_types: List of check types to run (default: all)
        - severity_threshold: Minimum severity to report (default: "low")
        - custom_rules: Custom security rules (extends defaults)

    Context Input:
        - code_context: Dict[file_path, code_lines]
        - parsed_diff: Optional diff information

    Context Output:
        - security_findings: List of security issues found
        - security_summary: Summary statistics
        - security_gate_status: PASS/WARN/FAIL
    """

    def prep(ctx, params):
        code_context = ctx.get("code_context", {})
        parsed_diff = ctx.get("parsed_diff", {})

        # Get security rules
        rules = _get_default_security_rules()

        # Merge with custom rules if provided
        custom_rules = params.get("custom_rules", {})
        if custom_rules:
            for rule_name, rule_config in custom_rules.items():
                if rule_name in rules:
                    # Extend patterns
                    rules[rule_name]["patterns"].extend(rule_config.get("patterns", []))
                else:
                    # Add new rule
                    rules[rule_name] = rule_config

        # Filter check types
        check_types = params.get("check_types")
        if check_types:
            rules = {k: v for k, v in rules.items() if k in check_types}

        return {
            "code_context": code_context,
            "parsed_diff": parsed_diff,
            "rules": rules,
            "severity_threshold": params.get("severity_threshold", "low")
        }

    def exec(prep_result, params):
        code_context = prep_result["code_context"]
        parsed_diff = prep_result["parsed_diff"]
        rules = prep_result["rules"]
        threshold = prep_result["severity_threshold"]

        findings = []

        # Analyze each file
        for file_path, code_lines in code_context.items():
            # Convert to list of strings if needed
            if isinstance(code_lines, list) and code_lines and isinstance(code_lines[0], str):
                code_lines_list = [line.rstrip('\n') for line in code_lines]
            else:
                code_lines_list = code_lines

            # Get changed line numbers if available
            changed_lines = set()
            if file_path in parsed_diff:
                changed_lines = set(parsed_diff[file_path].get("added_line_numbers", []))

            file_findings = _analyze_file(
                file_path,
                code_lines_list,
                rules,
                changed_lines
            )
            findings.extend(file_findings)

        # Filter by severity
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        threshold_value = severity_order.get(threshold, 0)
        findings = [
            f for f in findings
            if severity_order.get(f["severity"], 0) >= threshold_value
        ]

        # Sort by severity and line number
        findings.sort(
            key=lambda x: (
                -severity_order.get(x["severity"], 0),
                x["file"],
                x["line"]
            )
        )

        # Generate summary
        summary = _generate_summary(findings)

        # Determine gate status
        critical_count = summary["by_severity"].get("critical", 0)
        high_count = summary["by_severity"].get("high", 0)

        if critical_count > 0:
            gate_status = "FAIL"
            gate_reason = f"{critical_count} critical security issues found"
        elif high_count > params.get("max_high_issues", 3):
            gate_status = "WARN"
            gate_reason = f"{high_count} high severity issues found (threshold: {params.get('max_high_issues', 3)})"
        else:
            gate_status = "PASS"
            gate_reason = "No critical security issues"

        return {
            "success": True,
            "findings": findings,
            "summary": summary,
            "gate_status": gate_status,
            "gate_reason": gate_reason
        }

    def post(ctx, prep_result, exec_result, params):
        if exec_result["success"]:
            ctx["security_findings"] = exec_result["findings"]
            ctx["security_summary"] = exec_result["summary"]
            ctx["security_gate_status"] = exec_result["gate_status"]
            ctx["security_gate_reason"] = exec_result["gate_reason"]
            return "security_complete"
        else:
            ctx["security_error"] = exec_result.get("error", "Unknown error")
            return "security_failed"

    return node(prep=prep, exec=exec, post=post)


def _get_default_security_rules():
    """Default security patterns"""
    return {
        'sql_injection': {
            'patterns': [
                r'execute\s*\(\s*["\'].*%',
                r'cursor\.execute\s*\(\s*f["\']',
                r'\.raw\s*\(\s*["\'].*%',
                r'executemany\s*\(\s*["\'].*%',
                r'=\s*f["\'].*SELECT.*FROM',  # f-string with SQL
                r'=\s*f["\'].*INSERT.*INTO',  # f-string with INSERT
                r'=\s*f["\'].*UPDATE.*SET',   # f-string with UPDATE
                r'=\s*f["\'].*DELETE.*FROM',  # f-string with DELETE
            ],
            'severity': 'critical',
            'message': 'Potential SQL injection vulnerability. Use parameterized queries.'
        },
        'hardcoded_secrets': {
            'patterns': [
                r'API_KEY\s*=\s*["\'][^"\']{20,}',
                r'password\s*=\s*["\'](?!{{)[^"\']+["\']',
                r'SECRET\s*=\s*["\'][^"\']{20,}',
                r'TOKEN\s*=\s*["\'][^"\']{20,}',
                r'aws_secret_access_key\s*=',
            ],
            'severity': 'high',
            'message': 'Hardcoded secret detected. Use environment variables or secret management.'
        },
        'command_injection': {
            'patterns': [
                r'subprocess.*shell\s*=\s*True',
                r'os\.system\s*\(',
                r'eval\s*\(',
                r'exec\s*\(',
            ],
            'severity': 'critical',
            'message': 'Command injection risk. Avoid shell=True and eval/exec.'
        },
        'path_traversal': {
            'patterns': [
                r'open\s*\([^)]*\.\./[^)]*\)',
                r'os\.path\.join\([^)]*\.\./[^)]*\)',
            ],
            'severity': 'high',
            'message': 'Path traversal vulnerability. Validate and sanitize file paths.'
        },
        'unsafe_deserialization': {
            'patterns': [
                r'pickle\.loads?\s*\(',
                r'yaml\.unsafe_load\s*\(',
                r'yaml\.load\s*\([^,)]*\)',  # Without Loader
            ],
            'severity': 'critical',
            'message': 'Unsafe deserialization. Use yaml.safe_load() or avoid pickle.'
        },
        'weak_cryptography': {
            'patterns': [
                r'hashlib\.md5\s*\(',
                r'hashlib\.sha1\s*\(',
                r'Crypto\.Hash\.MD5',
                r'Crypto\.Hash\.SHA1',
            ],
            'severity': 'medium',
            'message': 'Weak cryptographic algorithm. Use SHA256 or better.'
        }
    }


def _analyze_file(file_path: str, code_lines: List[str], rules: Dict[str, Any], changed_lines: set) -> List[Dict[str, Any]]:
    """Analyze a single file for security issues"""
    findings = []

    for line_num, line in enumerate(code_lines, 1):
        # Skip comments and blank lines
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # Check each security rule
        for vuln_type, rule_config in rules.items():
            patterns = rule_config.get('patterns', [])
            severity = rule_config.get('severity', 'medium')
            message = rule_config.get('message', f'{vuln_type} detected')

            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    finding = {
                        'type': vuln_type,
                        'category': 'security',
                        'file': file_path,
                        'line': line_num,
                        'code': line.strip(),
                        'severity': severity,
                        'message': message,
                        'pattern': pattern
                    }

                    # Mark if this is in changed lines
                    if changed_lines and line_num in changed_lines:
                        finding['is_new'] = True

                    findings.append(finding)

    return findings


def _generate_summary(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics"""
    summary = {
        'total_issues': len(findings),
        'by_severity': {},
        'by_type': {},
        'by_file': {},
        'new_issues': 0
    }

    for finding in findings:
        # Count by severity
        severity = finding['severity']
        summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1

        # Count by type
        vuln_type = finding['type']
        summary['by_type'][vuln_type] = summary['by_type'].get(vuln_type, 0) + 1

        # Count by file
        file_path = finding['file']
        summary['by_file'][file_path] = summary['by_file'].get(file_path, 0) + 1

        # Count new issues
        if finding.get('is_new'):
            summary['new_issues'] += 1

    return summary
