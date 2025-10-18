from engine import node
import re
from typing import List, Dict, Any

def quality_review_node():
    """Code quality review node

    Checks for code quality issues:
    - Magic numbers
    - Deep nesting
    - Long functions
    - Missing docstrings
    - Commented code
    - Print statements (should use logging)
    - Broad exceptions
    - God classes

    Parameters:
        - check_types: List of check types to run (default: all)
        - max_function_lines: Max lines per function (default: 50)
        - max_nesting_depth: Max nesting depth (default: 3)
        - custom_rules: Custom quality rules (extends defaults)

    Context Input:
        - code_context: Dict[file_path, code_lines]
        - parsed_diff: Optional diff information

    Context Output:
        - quality_findings: List of quality issues found
        - quality_summary: Summary statistics
    """

    def prep(ctx, params):
        code_context = ctx.get("code_context", {})
        parsed_diff = ctx.get("parsed_diff", {})

        # Get quality rules
        rules = _get_default_quality_rules(params)

        # Merge with custom rules if provided
        custom_rules = params.get("custom_rules", {})
        if custom_rules:
            for rule_name, rule_config in custom_rules.items():
                if rule_name in rules:
                    # Update existing rule
                    rules[rule_name].update(rule_config)
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
            "max_function_lines": params.get("max_function_lines", 50),
            "max_nesting_depth": params.get("max_nesting_depth", 3)
        }

    def exec(prep_result, params):
        code_context = prep_result["code_context"]
        parsed_diff = prep_result["parsed_diff"]
        rules = prep_result["rules"]

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
                changed_lines,
                prep_result["max_function_lines"],
                prep_result["max_nesting_depth"]
            )
            findings.extend(file_findings)

        # Sort by severity and line number
        severity_order = {"high": 3, "medium": 2, "low": 1}
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
            ctx["quality_findings"] = exec_result["findings"]
            ctx["quality_summary"] = exec_result["summary"]
            return "quality_complete"
        else:
            ctx["quality_error"] = exec_result.get("error", "Unknown error")
            return "quality_failed"

    return node(prep=prep, exec=exec, post=post)


def _get_default_quality_rules(params):
    """Default quality patterns"""
    return {
        'magic_numbers': {
            'patterns': [
                r'(?<![a-zA-Z_])\d{2,}(?![a-zA-Z_])',  # Numbers with 2+ digits
            ],
            'severity': 'low',
            'message': 'Magic number detected. Consider using a named constant.',
            'exclude_patterns': [r'^\s*#', r'^\s*"""', r'^\s*\'\'\'']  # Exclude comments/docstrings
        },
        'deep_nesting': {
            'max_depth': params.get("max_nesting_depth", 3),
            'severity': 'medium',
            'message': 'Deeply nested code. Consider refactoring for better readability.'
        },
        'commented_code': {
            'patterns': [
                r'^\s*#\s*(def |class |if |for |while |return |import )',
            ],
            'severity': 'low',
            'message': 'Commented-out code found. Remove if not needed.'
        },
        'print_statements': {
            'patterns': [
                r'\bprint\s*\(',
            ],
            'severity': 'low',
            'message': 'Print statement found. Use logging instead.'
        },
        'broad_exceptions': {
            'patterns': [
                r'except\s*:\s*$',
                r'except\s+Exception\s*:\s*$',
            ],
            'severity': 'medium',
            'message': 'Broad exception handler. Catch specific exceptions.'
        },
        'missing_docstrings': {
            'check_functions': True,
            'check_classes': True,
            'severity': 'low',
            'message': 'Missing docstring. Add documentation for public APIs.'
        }
    }


def _analyze_file(file_path: str, code_lines: List[str], rules: Dict[str, Any],
                  changed_lines: set, max_function_lines: int, max_nesting_depth: int) -> List[Dict[str, Any]]:
    """Analyze a single file for quality issues"""
    findings = []
    current_function = None
    current_class = None
    nesting_depth = 0

    for line_num, line in enumerate(code_lines, 1):
        stripped = line.strip()

        # Track nesting depth
        indent = len(line) - len(line.lstrip())
        if stripped and not stripped.startswith('#'):
            # Approximate nesting by indentation level (4 spaces = 1 level)
            nesting_depth = indent // 4

        # Check for class definitions
        if stripped.startswith('class '):
            current_class = {
                'name': _extract_name(stripped, 'class'),
                'start_line': line_num,
                'has_docstring': False
            }

        # Check for function definitions
        if stripped.startswith('def '):
            current_function = {
                'name': _extract_name(stripped, 'def'),
                'start_line': line_num,
                'lines': 0,
                'has_docstring': False
            }

        # Check for docstrings
        if (stripped.startswith('"""') or stripped.startswith("'''")) and current_function:
            current_function['has_docstring'] = True
        if (stripped.startswith('"""') or stripped.startswith("'''")) and current_class:
            current_class['has_docstring'] = True

        # Count function lines
        if current_function:
            current_function['lines'] += 1

            # Check if function ended
            if stripped and not stripped.startswith('#') and indent == 0 and line_num > current_function['start_line']:
                # Function ended, check length
                if current_function['lines'] > max_function_lines:
                    findings.append({
                        'type': 'long_function',
                        'category': 'quality',
                        'file': file_path,
                        'line': current_function['start_line'],
                        'code': f"def {current_function['name']}",
                        'severity': 'medium',
                        'message': f"Function too long ({current_function['lines']} lines, max: {max_function_lines}). Consider breaking it down.",
                        'is_new': changed_lines and current_function['start_line'] in changed_lines
                    })

                # Check for missing docstring
                if 'missing_docstrings' in rules and not current_function['has_docstring']:
                    if not current_function['name'].startswith('_'):  # Skip private functions
                        findings.append({
                            'type': 'missing_docstrings',
                            'category': 'quality',
                            'file': file_path,
                            'line': current_function['start_line'],
                            'code': f"def {current_function['name']}",
                            'severity': rules['missing_docstrings']['severity'],
                            'message': rules['missing_docstrings']['message'],
                            'is_new': changed_lines and current_function['start_line'] in changed_lines
                        })

                current_function = None

        # Check deep nesting
        if 'deep_nesting' in rules and nesting_depth > rules['deep_nesting']['max_depth']:
            if stripped and not stripped.startswith('#'):
                findings.append({
                    'type': 'deep_nesting',
                    'category': 'quality',
                    'file': file_path,
                    'line': line_num,
                    'code': line.strip(),
                    'severity': rules['deep_nesting']['severity'],
                    'message': f"{rules['deep_nesting']['message']} (depth: {nesting_depth})",
                    'is_new': changed_lines and line_num in changed_lines
                })

        # Check pattern-based rules
        for rule_name, rule_config in rules.items():
            if 'patterns' not in rule_config:
                continue

            patterns = rule_config['patterns']
            severity = rule_config.get('severity', 'low')
            message = rule_config.get('message', f'{rule_name} detected')
            exclude_patterns = rule_config.get('exclude_patterns', [])

            # Check if line should be excluded
            should_exclude = False
            for exclude_pattern in exclude_patterns:
                if re.search(exclude_pattern, line):
                    should_exclude = True
                    break

            if should_exclude:
                continue

            for pattern in patterns:
                if re.search(pattern, line):
                    findings.append({
                        'type': rule_name,
                        'category': 'quality',
                        'file': file_path,
                        'line': line_num,
                        'code': line.strip(),
                        'severity': severity,
                        'message': message,
                        'pattern': pattern,
                        'is_new': changed_lines and line_num in changed_lines
                    })

    return findings


def _extract_name(line: str, keyword: str) -> str:
    """Extract function or class name from definition line"""
    match = re.search(rf'{keyword}\s+(\w+)', line)
    return match.group(1) if match else 'unknown'


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
        issue_type = finding['type']
        summary['by_type'][issue_type] = summary['by_type'].get(issue_type, 0) + 1

        # Count by file
        file_path = finding['file']
        summary['by_file'][file_path] = summary['by_file'].get(file_path, 0) + 1

        # Count new issues
        if finding.get('is_new'):
            summary['new_issues'] += 1

    return summary
