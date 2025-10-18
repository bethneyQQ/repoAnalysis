from engine import node
import yaml
import json
from typing import List, Dict, Any

def aggregate_findings_node():
    """Aggregate findings from all review nodes

    Parameters:
        - output_format: Format for output ('yaml', 'json', 'markdown')
        - include_summaries: Include individual summaries (default: True)

    Context Input:
        - security_findings: Security issues
        - quality_findings: Quality issues
        - performance_findings: Performance issues
        - security_summary: Security summary
        - quality_summary: Quality summary
        - performance_summary: Performance summary

    Context Output:
        - all_findings: Combined list of all findings
        - overall_summary: Overall statistics
        - formatted_report: Formatted report string
    """

    def prep(ctx, params):
        return {
            "security_findings": ctx.get("security_findings", []),
            "quality_findings": ctx.get("quality_findings", []),
            "performance_findings": ctx.get("performance_findings", []),
            "security_summary": ctx.get("security_summary", {}),
            "quality_summary": ctx.get("quality_summary", {}),
            "performance_summary": ctx.get("performance_summary", {}),
            "security_gate_status": ctx.get("security_gate_status", "N/A"),
            "security_gate_reason": ctx.get("security_gate_reason", ""),
            "output_format": params.get("output_format", "yaml"),
            "include_summaries": params.get("include_summaries", True)
        }

    def exec(prep_result, params):
        # Combine all findings
        all_findings = []
        all_findings.extend(prep_result["security_findings"])
        all_findings.extend(prep_result["quality_findings"])
        all_findings.extend(prep_result["performance_findings"])

        # Sort by severity, category, file, line
        severity_order = {"critical": 5, "high": 4, "medium": 3, "low": 2}
        all_findings.sort(
            key=lambda x: (
                -severity_order.get(x.get("severity", "low"), 0),
                x.get("category", ""),
                x.get("file", ""),
                x.get("line", 0)
            )
        )

        # Generate overall summary
        overall_summary = _generate_overall_summary(
            prep_result["security_summary"],
            prep_result["quality_summary"],
            prep_result["performance_summary"]
        )

        # Format report
        output_format = prep_result["output_format"]
        include_summaries = prep_result["include_summaries"]

        formatted_report = _format_report(
            all_findings,
            overall_summary,
            {
                "security": prep_result["security_summary"],
                "quality": prep_result["quality_summary"],
                "performance": prep_result["performance_summary"]
            },
            prep_result["security_gate_status"],
            prep_result["security_gate_reason"],
            output_format,
            include_summaries
        )

        return {
            "success": True,
            "all_findings": all_findings,
            "overall_summary": overall_summary,
            "formatted_report": formatted_report
        }

    def post(ctx, prep_result, exec_result, params):
        if exec_result["success"]:
            ctx["all_findings"] = exec_result["all_findings"]
            ctx["overall_summary"] = exec_result["overall_summary"]
            ctx["formatted_report"] = exec_result["formatted_report"]
            return "aggregation_complete"
        else:
            ctx["aggregation_error"] = exec_result.get("error", "Unknown error")
            return "aggregation_failed"

    return node(prep=prep, exec=exec, post=post)


def _generate_overall_summary(security_summary, quality_summary, performance_summary):
    """Generate overall summary from individual summaries"""
    overall = {
        "total_issues": 0,
        "by_category": {
            "security": security_summary.get("total_issues", 0),
            "quality": quality_summary.get("total_issues", 0),
            "performance": performance_summary.get("total_issues", 0)
        },
        "by_severity": {},
        "new_issues": 0
    }

    # Aggregate severity counts
    for summary in [security_summary, quality_summary, performance_summary]:
        for severity, count in summary.get("by_severity", {}).items():
            overall["by_severity"][severity] = overall["by_severity"].get(severity, 0) + count
        overall["new_issues"] += summary.get("new_issues", 0)

    overall["total_issues"] = sum(overall["by_category"].values())

    return overall


def _format_report(all_findings, overall_summary, category_summaries,
                   security_gate_status, security_gate_reason,
                   output_format, include_summaries):
    """Format findings into specified format"""

    if output_format == "yaml":
        return _format_yaml(
            all_findings, overall_summary, category_summaries,
            security_gate_status, security_gate_reason, include_summaries
        )
    elif output_format == "json":
        return _format_json(
            all_findings, overall_summary, category_summaries,
            security_gate_status, security_gate_reason, include_summaries
        )
    else:  # markdown
        return _format_markdown(
            all_findings, overall_summary, category_summaries,
            security_gate_status, security_gate_reason, include_summaries
        )


def _format_yaml(all_findings, overall_summary, category_summaries,
                 security_gate_status, security_gate_reason, include_summaries):
    """Format as YAML"""
    report = {
        "code_review_report": {
            "security_gate": {
                "status": security_gate_status,
                "reason": security_gate_reason
            },
            "overall_summary": overall_summary
        }
    }

    if include_summaries:
        report["code_review_report"]["category_summaries"] = category_summaries

    report["code_review_report"]["findings"] = all_findings

    return yaml.dump(report, default_flow_style=False, allow_unicode=True)


def _format_json(all_findings, overall_summary, category_summaries,
                 security_gate_status, security_gate_reason, include_summaries):
    """Format as JSON"""
    report = {
        "code_review_report": {
            "security_gate": {
                "status": security_gate_status,
                "reason": security_gate_reason
            },
            "overall_summary": overall_summary
        }
    }

    if include_summaries:
        report["code_review_report"]["category_summaries"] = category_summaries

    report["code_review_report"]["findings"] = all_findings

    return json.dumps(report, indent=2, ensure_ascii=False)


def _format_markdown(all_findings, overall_summary, category_summaries,
                     security_gate_status, security_gate_reason, include_summaries):
    """Format as Markdown"""
    lines = []

    # Header
    lines.append("# Code Review Report")
    lines.append("")

    # Security Gate
    lines.append("## Security Gate")
    status_emoji = {"PASS": "PASS", "WARN": "WARN", "FAIL": "FAIL", "N/A": "N/A"}
    lines.append(f"**Status**: {status_emoji.get(security_gate_status, security_gate_status)}")
    lines.append(f"**Reason**: {security_gate_reason}")
    lines.append("")

    # Overall Summary
    lines.append("## Overall Summary")
    lines.append("")
    lines.append(f"- **Total Issues**: {overall_summary['total_issues']}")
    lines.append(f"- **New Issues**: {overall_summary['new_issues']}")
    lines.append("")
    lines.append("### By Category")
    for category, count in overall_summary["by_category"].items():
        lines.append(f"- **{category.capitalize()}**: {count}")
    lines.append("")
    lines.append("### By Severity")
    for severity in ["critical", "high", "medium", "low"]:
        count = overall_summary["by_severity"].get(severity, 0)
        if count > 0:
            lines.append(f"- **{severity.capitalize()}**: {count}")
    lines.append("")

    # Category Summaries
    if include_summaries:
        lines.append("## Category Summaries")
        lines.append("")

        for category_name, summary in category_summaries.items():
            if summary.get("total_issues", 0) > 0:
                lines.append(f"### {category_name.capitalize()}")
                lines.append(f"- Total: {summary['total_issues']}")
                lines.append(f"- New: {summary.get('new_issues', 0)}")
                lines.append("")

    # Findings
    lines.append("## Findings")
    lines.append("")

    if not all_findings:
        lines.append("No issues found.")
    else:
        current_file = None
        for finding in all_findings:
            # Group by file
            if finding["file"] != current_file:
                current_file = finding["file"]
                lines.append(f"### {current_file}")
                lines.append("")

            # Finding details
            severity = finding["severity"].upper()
            line_num = finding["line"]
            issue_type = finding["type"]
            message = finding["message"]
            code = finding.get("code", "")
            is_new = " (NEW)" if finding.get("is_new") else ""

            lines.append(f"**Line {line_num}** - [{severity}] {issue_type}{is_new}")
            lines.append(f"- {message}")
            if code:
                lines.append(f"- Code: `{code}`")
            lines.append("")

    return "\n".join(lines)
