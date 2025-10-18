from engine import node
import re
from typing import List, Dict, Any

def performance_review_node():
    """Performance issue detection node

    Checks for common performance issues:
    - Nested loops (quadratic complexity)
    - String concatenation in loops
    - Missing database indexes hints
    - N+1 query patterns
    - Loading all data without pagination
    - Blocking operations in async code

    Parameters:
        - check_types: List of check types to run (default: all)
        - custom_rules: Custom performance rules (extends defaults)

    Context Input:
        - code_context: Dict[file_path, code_lines]
        - parsed_diff: Optional diff information

    Context Output:
        - performance_findings: List of performance issues found
        - performance_summary: Summary statistics
    """

    def prep(ctx, params):
        code_context = ctx.get("code_context", {})
        parsed_diff = ctx.get("parsed_diff", {})

        # Get performance rules
        rules = _get_default_performance_rules()

        # Merge with custom rules if provided
        custom_rules = params.get("custom_rules", {})
        if custom_rules:
            for rule_name, rule_config in custom_rules.items():
                if rule_name in rules:
                    # Extend patterns
                    if "patterns" in rule_config:
                        rules[rule_name]["patterns"].extend(rule_config["patterns"])
                    rules[rule_name].update({k: v for k, v in rule_config.items() if k != "patterns"})
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
            "rules": rules
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
                changed_lines
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
            ctx["performance_findings"] = exec_result["findings"]
            ctx["performance_summary"] = exec_result["summary"]
            return "performance_complete"
        else:
            ctx["performance_error"] = exec_result.get("error", "Unknown error")
            return "performance_failed"

    return node(prep=prep, exec=exec, post=post)


def _get_default_performance_rules():
    """Default performance patterns"""
    return {
        'nested_loops': {
            'check_nesting': True,
            'severity': 'medium',
            'message': 'Nested loops detected. Consider optimizing for better performance (potential O(n²)).'
        },
        'string_concat_in_loop': {
            'patterns': [
                r'(for|while).*:\s*\n.*\w+\s*\+=\s*["\']',
                r'(for|while).*:\s*\n.*\w+\s*=\s*\w+\s*\+\s*["\']',
            ],
            'severity': 'medium',
            'message': 'String concatenation in loop. Use join() or list comprehension.'
        },
        'loading_all_data': {
            'patterns': [
                r'\.all\(\)\s*$',
                r'\.filter\(\)\.all\(\)',
                r'SELECT\s+\*\s+FROM',
            ],
            'severity': 'medium',
            'message': 'Loading all data without pagination. Consider using pagination or limits.'
        },
        'n_plus_one_hint': {
            'patterns': [
                r'for\s+\w+\s+in\s+\w+:\s*\n.*\.get\(',
                r'for\s+\w+\s+in\s+\w+:\s*\n.*\.filter\(',
            ],
            'severity': 'high',
            'message': 'Potential N+1 query pattern. Consider using select_related() or prefetch_related().'
        },
        'blocking_in_async': {
            'patterns': [
                r'async\s+def\s+.*:\s*\n.*time\.sleep\(',
                r'async\s+def\s+.*:\s*\n.*requests\.',
            ],
            'severity': 'high',
            'message': 'Blocking operation in async function. Use async alternatives (asyncio.sleep, aiohttp).'
        },
        'inefficient_search': {
            'patterns': [
                r'\w+\s+in\s+\[.*for.*in',  # 'x in [list comprehension]'
            ],
            'severity': 'low',
            'message': 'Inefficient membership test. Convert list comprehension to set for O(1) lookups.'
        }
    }


def _analyze_file(file_path: str, code_lines: List[str], rules: Dict[str, Any], changed_lines: set) -> List[Dict[str, Any]]:
    """Analyze a single file for performance issues"""
    findings = []
    loop_stack = []  # Track nested loops

    for line_num, line in enumerate(code_lines, 1):
        stripped = line.strip()

        # Track loop nesting
        indent = len(line) - len(line.lstrip())

        # Check for loop start
        if re.match(r'(for|while)\s+', stripped):
            # Pop loops with higher or equal indentation
            while loop_stack and loop_stack[-1]['indent'] >= indent:
                loop_stack.pop()

            loop_stack.append({
                'type': 'for' if stripped.startswith('for') else 'while',
                'line': line_num,
                'indent': indent
            })

            # Check for nested loops
            if 'nested_loops' in rules and len(loop_stack) >= 2:
                findings.append({
                    'type': 'nested_loops',
                    'category': 'performance',
                    'file': file_path,
                    'line': line_num,
                    'code': line.strip(),
                    'severity': rules['nested_loops']['severity'],
                    'message': f"{rules['nested_loops']['message']} (nesting level: {len(loop_stack)})",
                    'is_new': changed_lines and line_num in changed_lines
                })

        # Pop loops when indentation decreases
        if stripped and not stripped.startswith('#'):
            while loop_stack and loop_stack[-1]['indent'] >= indent and not re.match(r'(for|while)\s+', stripped):
                loop_stack.pop()

        # Check pattern-based rules
        for rule_name, rule_config in rules.items():
            if 'patterns' not in rule_config:
                continue

            patterns = rule_config['patterns']
            severity = rule_config.get('severity', 'medium')
            message = rule_config.get('message', f'{rule_name} detected')

            # For multi-line patterns, combine with next line
            context_line = line
            if line_num < len(code_lines):
                next_line = code_lines[line_num] if line_num < len(code_lines) else ""
                context_line = line + '\n' + next_line

            for pattern in patterns:
                if re.search(pattern, context_line):
                    findings.append({
                        'type': rule_name,
                        'category': 'performance',
                        'file': file_path,
                        'line': line_num,
                        'code': line.strip(),
                        'severity': severity,
                        'message': message,
                        'pattern': pattern,
                        'is_new': changed_lines and line_num in changed_lines
                    })

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
        issue_type = finding['type']
        summary['by_type'][issue_type] = summary['by_type'].get(issue_type, 0) + 1

        # Count by file
        file_path = finding['file']
        summary['by_file'][file_path] = summary['by_file'].get(file_path, 0) + 1

        # Count new issues
        if finding.get('is_new'):
            summary['new_issues'] += 1

    return summary
