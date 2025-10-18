# Implementation Example: From CodeReviewAgent to Node

## Complete Example: Security Review Node

This document shows a complete, working example of converting CodeReviewAgent's security analysis into a reusable node.

---

## 1. Original CodeReviewAgent Structure

```python
# code_review_agent/analyzers/security_analyzer.py (simplified)
class SecurityAnalyzer:
    def __init__(self):
        self.patterns = {
            'sql_injection': [
                r'execute\s*\(\s*["\'].*%',
                r'cursor\.execute\s*\(\s*f["\']'
            ],
            'hardcoded_secrets': [
                r'API_KEY\s*=\s*["\'][^"\']{20,}',
                r'password\s*=\s*["\'](?!{{)'
            ],
            'command_injection': [
                r'subprocess.*shell\s*=\s*True',
                r'os\.system\s*\(',
                r'eval\s*\(',
                r'exec\s*\('
            ]
        }

    def analyze(self, code_lines, file_path):
        findings = []
        for line_num, line in enumerate(code_lines, 1):
            for vuln_type, patterns in self.patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line):
                        findings.append({
                            'type': vuln_type,
                            'file': file_path,
                            'line': line_num,
                            'code': line.strip(),
                            'severity': self._get_severity(vuln_type)
                        })
        return findings

    def _get_severity(self, vuln_type):
        severity_map = {
            'sql_injection': 'critical',
            'hardcoded_secrets': 'high',
            'command_injection': 'critical'
        }
        return severity_map.get(vuln_type, 'medium')
```

---

## 2. Converted to Node Architecture

### File: `nodes/common/review/security_review_node.py`

```python
from engine import node
import re
from typing import List, Dict, Any

def security_review_node():
    """Security vulnerability detection node

    Checks for common security issues:
    - SQL injection
    - Hardcoded secrets
    - Command injection
    - XSS vulnerabilities
    - Path traversal
    - Unsafe deserialization

    Parameters:
        - check_types: List of check types to run (default: all)
        - severity_threshold: Minimum severity to report (default: "low")
        - rules: Custom security rules (overrides defaults)

    Context Input:
        - code_context: Dict[file_path, code_lines]
        - constraint_rules: Optional custom rules

    Context Output:
        - security_findings: List of security issues found
        - security_summary: Summary statistics
    """

    def prep(ctx, params):
        # Get code to analyze
        code_context = ctx.get("code_context", {})
        file_changes = ctx.get("file_changes", {})

        # Load security rules (from params, context, or defaults)
        rules = params.get("rules") or \
                ctx.get("constraint_rules", {}).get("security", {}) or \
                _get_default_security_rules()

        # Filter check types
        check_types = params.get("check_types", list(rules.keys()))

        return {
            "code_context": code_context,
            "file_changes": file_changes,
            "rules": {k: v for k, v in rules.items() if k in check_types},
            "severity_threshold": params.get("severity_threshold", "low")
        }

    def exec(prep_result, params):
        code_context = prep_result["code_context"]
        rules = prep_result["rules"]
        threshold = prep_result["severity_threshold"]

        findings = []

        # Analyze each file
        for file_path, code_lines in code_context.items():
            file_findings = _analyze_file(file_path, code_lines, rules)
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

        return {
            "success": True,
            "findings": findings,
            "summary": summary
        }

    def post(ctx, prep_result, exec_result, params):
        if exec_result["success"]:
            ctx["security_findings"] = exec_result["findings"]
            ctx["security_summary"] = exec_result["summary"]

            # Set gate status based on findings
            critical_count = exec_result["summary"]["by_severity"].get("critical", 0)
            high_count = exec_result["summary"]["by_severity"].get("high", 0)

            if critical_count > 0:
                ctx["security_gate_status"] = "FAIL"
                ctx["security_gate_reason"] = f"{critical_count} critical security issues found"
            elif high_count > params.get("max_high_issues", 3):
                ctx["security_gate_status"] = "WARN"
                ctx["security_gate_reason"] = f"{high_count} high severity issues found"
            else:
                ctx["security_gate_status"] = "PASS"
                ctx["security_gate_reason"] = "No critical security issues"

            return "security_complete"
        else:
            ctx["security_error"] = exec_result.get("error", "Unknown error")
            return "security_failed"

    return node(prep=prep, exec=exec, post=post)


# Helper functions

def _get_default_security_rules():
    """Default security patterns"""
    return {
        'sql_injection': {
            'patterns': [
                r'execute\s*\(\s*["\'].*%',
                r'cursor\.execute\s*\(\s*f["\']',
                r'\.raw\s*\(\s*["\'].*%',
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
                r'open\s*\(\s*[^)]*\.\./[^)]*\)',
                r'os\.path\.join\s*\([^)]*\.\./[^)]*\)',
            ],
            'severity': 'high',
            'message': 'Path traversal vulnerability. Validate and sanitize file paths.'
        },
        'unsafe_deserialization': {
            'patterns': [
                r'pickle\.loads?\s*\(',
                r'yaml\.load\s*\(',
                r'eval\s*\(',
            ],
            'severity': 'critical',
            'message': 'Unsafe deserialization. Use safe alternatives.'
        }
    }


def _analyze_file(file_path: str, code_lines: List[str], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
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
                    findings.append({
                        'type': vuln_type,
                        'file': file_path,
                        'line': line_num,
                        'code': line.strip(),
                        'severity': severity,
                        'message': message,
                        'pattern': pattern
                    })

    return findings


def _generate_summary(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics"""
    summary = {
        'total_issues': len(findings),
        'by_severity': {},
        'by_type': {},
        'by_file': {}
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

    return summary
```

---

## 3. Usage Examples

### Example 1: Standalone Security Review

```python
from engine import flow
from nodes.common.review import security_review_node

# Create a simple flow
f = flow()
f.add(security_review_node(), name="security", params={
    "check_types": ["sql_injection", "command_injection"],
    "severity_threshold": "medium"
})

# Run with code context
result = f.run({
    "code_context": {
        "app.py": [
            "cursor.execute(f'SELECT * FROM users WHERE id={user_id}')",
            "os.system('rm -rf ' + file_path)",
            "password = 'hardcoded123'"
        ]
    }
})

# Check results
findings = result.get("security_findings", [])
for finding in findings:
    print(f"{finding['severity'].upper()}: {finding['file']}:{finding['line']}")
    print(f"  {finding['message']}")
    print(f"  Code: {finding['code']}\n")
```

### Example 2: In Code Review Scenario

```python
# scenarios/scenario_6_code_review.py
from engine import flow
from nodes.common import get_git_diff_node, parse_diff_node
from nodes.common.review import security_review_node

def create_code_review_scenario(config):
    f = flow()

    # Get diff
    f.add(get_git_diff_node(), name="get_diff", params={
        "git_ref": config.get("git_ref", "HEAD")
    })

    # Parse diff
    f.add(parse_diff_node(), name="parse")

    # Security review
    f.add(security_review_node(), name="security", params={
        "severity_threshold": "low"
    })

    # ... more review nodes ...

    return f
```

### Example 3: Custom Rules

```python
# With custom security rules
custom_rules = {
    'deprecated_crypto': {
        'patterns': [
            r'hashlib\.md5\s*\(',
            r'hashlib\.sha1\s*\(',
        ],
        'severity': 'medium',
        'message': 'Deprecated crypto algorithm. Use SHA256 or better.'
    }
}

f = flow()
f.add(security_review_node(), name="security", params={
    "rules": custom_rules
})

result = f.run({"code_context": {...}})
```

---

## 4. Integration with Existing Scenarios

### Scenario 3: Regression + Security

```python
# scenarios/scenario_3_regression.py (enhanced)
from nodes.common.review import security_review_node

def create_regression_scenario(config):
    f = flow()

    # ... existing regression nodes ...

    # Add security check for new code
    f.add(get_git_diff_node(), name="get_changes", params={
        "git_ref": "HEAD"
    })

    f.add(security_review_node(), name="security_scan", params={
        "check_types": ["sql_injection", "command_injection", "hardcoded_secrets"],
        "severity_threshold": "high"
    })

    # Gate decision considers both test results and security
    f.add(call_llm_node(), name="gate_decision", params={
        "prompt_file": "prompts/regression_with_security.prompt.md",
        "model": config.get("model", "claude-3-haiku-20240307")
    })

    return f
```

---

## 5. Testing

```python
# tests/test_security_review_node.py
import pytest
from nodes.common.review.security_review_node import security_review_node
from engine import flow

def test_sql_injection_detection():
    f = flow()
    f.add(security_review_node(), name="security")

    result = f.run({
        "code_context": {
            "test.py": [
                "cursor.execute(f'SELECT * FROM users WHERE id={user_id}')"
            ]
        }
    })

    findings = result.get("security_findings", [])
    assert len(findings) == 1
    assert findings[0]["type"] == "sql_injection"
    assert findings[0]["severity"] == "critical"


def test_custom_rules():
    custom_rules = {
        'test_rule': {
            'patterns': [r'bad_function\s*\('],
            'severity': 'high',
            'message': 'bad_function is not allowed'
        }
    }

    f = flow()
    f.add(security_review_node(), name="security", params={
        "rules": custom_rules
    })

    result = f.run({
        "code_context": {
            "test.py": ["bad_function(arg)"]
        }
    })

    findings = result.get("security_findings", [])
    assert len(findings) == 1
    assert findings[0]["type"] == "test_rule"
```

---

## 6. CLI Integration

```python
# cli.py
@cli.command(name='security-scan')
@click.option('--git-diff', is_flag=True, help='Scan git diff')
@click.option('--files', multiple=True, help='Specific files to scan')
@click.option('--severity', default='low', help='Minimum severity threshold')
def security_scan(git_diff, files, severity):
    """Quick security scan"""
    from engine import flow
    from nodes.common.review import security_review_node

    f = flow()

    if git_diff:
        # Add git diff nodes
        pass

    f.add(security_review_node(), name="security", params={
        "severity_threshold": severity
    })

    result = f.run({"code_context": ...})

    # Display results
    findings = result.get("security_findings", [])
    summary = result.get("security_summary", {})

    click.echo(f"Found {summary['total_issues']} security issues")
    for finding in findings:
        click.echo(f"{finding['severity']}: {finding['file']}:{finding['line']}")
        click.echo(f"  {finding['message']}")
```

---

## Summary

This example demonstrates:

1. **Node Structure**: prep/exec/post phases
2. **Reusability**: Can be used in multiple scenarios
3. **Configurability**: Accepts parameters for customization
4. **Context Integration**: Reads from and writes to shared context
5. **Testing**: Easy to unit test
6. **CLI Integration**: Simple to expose via CLI

The same pattern applies to all other CodeReviewAgent analyzers:
- `performance_review_node`
- `quality_review_node`
- `constraint_validation_node`
- etc.
