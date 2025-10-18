"""
Scenario 6: Code Review Pipeline

Comprehensive code review with security, quality, and performance checks.
Integrates CodeReviewAgent capabilities into the Flow/Node architecture.
"""

from engine import flow
from nodes.common.diff import get_git_diff_node, parse_diff_node
from nodes.common.review import (
    security_review_node,
    quality_review_node,
    performance_review_node,
    aggregate_findings_node
)


def create_code_review_scenario(config):
    """Create code review scenario

    Configuration:
        - git_ref: Git reference to diff against (e.g., 'HEAD~1', 'main')
        - diff_file: Path to diff/patch file (alternative to git_ref)
        - security_checks: List of security checks to run (default: all)
        - quality_checks: List of quality checks to run (default: all)
        - performance_checks: List of performance checks to run (default: all)
        - max_high_issues: Max high severity security issues before FAIL (default: 3)
        - output_format: Report format ('yaml', 'json', 'markdown')
        - output_file: Path to save report (optional)
    """
    f = flow()

    # Phase 1: Get diff
    f.add(get_git_diff_node(), name="get_diff", params={
        "git_ref": config.get("git_ref"),
        "diff_file": config.get("diff_file"),
        "include_staged": config.get("include_staged", False)
    })

    # Phase 2: Parse diff
    f.add(parse_diff_node(), name="parse_diff")

    # Phase 3: Security Review
    f.add(security_review_node(), name="security_review", params={
        "check_types": config.get("security_checks"),
        "max_high_issues": config.get("max_high_issues", 3),
        "custom_rules": config.get("custom_security_rules")
    })

    # Phase 4: Quality Review (skip if disabled)
    quality_checks = config.get("quality_checks")
    if quality_checks is None or len(quality_checks) > 0:
        f.add(quality_review_node(), name="quality_review", params={
            "check_types": quality_checks,
            "max_function_lines": config.get("max_function_lines", 50),
            "max_nesting_depth": config.get("max_nesting_depth", 3),
            "custom_rules": config.get("custom_quality_rules")
        })

    # Phase 5: Performance Review (skip if disabled)
    performance_checks = config.get("performance_checks")
    if performance_checks is None or len(performance_checks) > 0:
        f.add(performance_review_node(), name="performance_review", params={
            "check_types": performance_checks,
            "custom_rules": config.get("custom_performance_rules")
        })

    # Phase 6: Aggregate Findings
    f.add(aggregate_findings_node(), name="aggregate_findings", params={
        "output_format": config.get("output_format", "yaml"),
        "include_summaries": config.get("include_summaries", True)
    })

    return f


def run(config):
    """Run code review scenario

    Args:
        config: Configuration dict

    Returns:
        Result context with findings and report
    """
    scenario = create_code_review_scenario(config)

    # Initialize context
    shared_store = {
        "project_root": config.get("project_root", ".")
    }

    # Run scenario
    result = scenario.run(shared_store)

    # Save report to file if specified
    output_file = config.get("output_file")
    if output_file and "formatted_report" in result:
        from pathlib import Path
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result["formatted_report"])

        result["output_file_path"] = str(output_path)

    return result


def run_quick_security_scan(git_ref=None, diff_file=None, project_root="."):
    """Quick security-only scan

    Args:
        git_ref: Git reference (e.g., 'HEAD~1')
        diff_file: Diff file path
        project_root: Project root directory

    Returns:
        Result with security findings
    """
    config = {
        "git_ref": git_ref,
        "diff_file": diff_file,
        "project_root": project_root,
        "quality_checks": [],  # Disable quality checks
        "performance_checks": [],  # Disable performance checks
        "output_format": "markdown"
    }

    return run(config)


def run_full_review(git_ref=None, diff_file=None, project_root=".", output_file=None):
    """Full code review with all checks

    Args:
        git_ref: Git reference (e.g., 'HEAD~1')
        diff_file: Diff file path
        project_root: Project root directory
        output_file: Where to save the report

    Returns:
        Result with all findings
    """
    config = {
        "git_ref": git_ref,
        "diff_file": diff_file,
        "project_root": project_root,
        "output_file": output_file,
        "output_format": "yaml"
    }

    return run(config)


if __name__ == "__main__":
    import sys

    print("=" * 80)
    print("Scenario 6: Code Review Pipeline")
    print("=" * 80)
    print()

    # Example usage
    if len(sys.argv) > 1:
        # Use provided diff file or git ref
        arg = sys.argv[1]
        if arg.endswith('.patch') or arg.endswith('.diff'):
            result = run_full_review(diff_file=arg, output_file="review_report.yaml")
        else:
            result = run_full_review(git_ref=arg, output_file="review_report.yaml")
    else:
        # Default: review working directory changes
        result = run_full_review(git_ref=None, output_file="review_report.yaml")

    # Display summary
    overall_summary = result.get("overall_summary", {})
    security_gate = result.get("security_gate_status", "N/A")

    print(f"Security Gate: {security_gate}")
    print(f"Total Issues: {overall_summary.get('total_issues', 0)}")
    print(f"New Issues: {overall_summary.get('new_issues', 0)}")
    print()

    print("By Category:")
    for category, count in overall_summary.get("by_category", {}).items():
        print(f"  - {category.capitalize()}: {count}")
    print()

    print("By Severity:")
    for severity in ["critical", "high", "medium", "low"]:
        count = overall_summary.get("by_severity", {}).get(severity, 0)
        if count > 0:
            print(f"  - {severity.capitalize()}: {count}")

    print()
    print("=" * 80)
    if "output_file_path" in result:
        print(f"Report saved to: {result['output_file_path']}")
    print("=" * 80)
