# Architecture Comparison: CodeReviewAgent vs repoAnalysis

## Quick Summary

**Yes, both repositories can be abstracted into the Node/Scenario workflow architecture!**

The key insight is that CodeReviewAgent's 7-phase pipeline maps naturally to a Flow composed of specialized Nodes.

---

## Side-by-Side Comparison

### CodeReviewAgent (Current Architecture)

```
PocketFlow-based Pipeline
    |
    v
[Triage] → [Semantic] → [Security] → [Performance] → [Quality] → [Constraint] → [Test/Docs]
    |           |            |              |              |             |            |
    v           v            v              v              v             v            v
  Output → LLM Analysis → Pattern Matching → Complexity Check → Rule Validation → Report
```

**Characteristics**:
- Linear 7-phase pipeline
- Each phase is a specialized analyzer
- LLM-powered semantic analysis
- Rule-based constraint checking
- Single output: Code review report

### repoAnalysis (Current Architecture)

```
Flow/Node Architecture
    |
    v
[Scenario 1-5] = Flow( Node1 + Node2 + ... + NodeN )
    |
    v
Each Node: prep() → exec() → post()
    |
    v
Shared Context Store → Results
```

**Characteristics**:
- Pluggable Flow/Node system
- 5 independent scenarios
- Reusable common nodes
- Custom nodes per scenario
- Multiple output formats

---

## Mapping CodeReviewAgent to Node/Scenario

### Before (CodeReviewAgent Original)

```python
# Monolithic pipeline in code_review_agent/flow.py
class ReviewFlow:
    def run(self, diff):
        triage_result = TriageAnalyzer().analyze(diff)
        semantic_result = SemanticAnalyzer().analyze(diff, triage_result)
        security_result = SecurityAnalyzer().analyze(diff)
        # ... more phases ...
        return format_report(all_results)
```

### After (Node-based Design)

```python
# scenarios/scenario_6_code_review.py
def create_code_review_scenario(config):
    f = flow()

    # Phase 0: Input
    f.add(get_git_diff_node(), name="get_diff")
    f.add(parse_diff_node(), name="parse_diff")

    # Phase 1: Triage
    f.add(triage_changes_node(), name="triage")

    # Phase 2-7: Reviews
    f.add(semantic_review_node(), name="semantic")
    f.add(security_review_node(), name="security")
    f.add(performance_review_node(), name="performance")
    f.add(quality_review_node(), name="quality")
    f.add(constraint_validation_node(), name="constraints")
    f.add(test_coverage_review_node(), name="tests")
    f.add(documentation_review_node(), name="docs")

    # Phase 8: Reporting
    f.add(aggregate_findings_node(), name="aggregate")
    f.add(format_review_report_node(), name="report")

    return f
```

---

## Node Decomposition

### 1. Input Processing Nodes

| Node | Purpose | Input | Output |
|------|---------|-------|--------|
| `get_git_diff_node` | Extract diff | git_ref, diff_file | diff_content, changed_files |
| `parse_diff_node` | Parse diff structure | diff_content | file_changes (added/removed/modified) |
| `extract_code_context_node` | Get surrounding code | changed_files, file_changes | code_context_per_file |
| `load_constraints_node` | Load review rules | rules_file | constraint_rules |

### 2. Analysis Nodes

| Node | Purpose | LLM? | Pattern? |
|------|---------|------|----------|
| `triage_changes_node` | Classify change type & risk | Yes | No |
| `semantic_review_node` | Logic & behavior analysis | Yes | No |
| `security_review_node` | Vulnerability detection | Yes | Yes |
| `performance_review_node` | Performance issues | Yes | Yes |
| `quality_review_node` | Code quality patterns | No | Yes |
| `constraint_validation_node` | Rule enforcement | No | Yes |
| `test_coverage_review_node` | Test gaps | Yes | Yes |
| `documentation_review_node` | Doc completeness | Yes | Yes |

### 3. Output Nodes

| Node | Purpose | Input | Output |
|------|---------|-------|--------|
| `aggregate_findings_node` | Merge all findings | All review results | aggregated_findings |
| `format_review_report_node` | Generate report | aggregated_findings | YAML/JSON/MD report |

---

## Workflow Examples

### Example 1: Full Code Review

```python
from scenarios.scenario_6_code_review import run_code_review

result = run_code_review(
    diff_file="changes.patch",
    rules_file="docs/code_review_rules.yaml",
    model="claude-3-haiku-20240307"
)

print(result.get("review_report"))
```

### Example 2: Security-Only Review

```python
from engine import flow
from nodes.common.review import (
    get_git_diff_node,
    parse_diff_node,
    security_review_node,
    format_review_report_node
)

f = flow()
f.add(get_git_diff_node(), name="get_diff")
f.add(parse_diff_node(), name="parse")
f.add(security_review_node(), name="security")
f.add(format_review_report_node(), name="report")

result = f.run({"git_ref": "HEAD"})
```

### Example 3: Integrate Security Scan into Regression Scenario

```python
# scenarios/scenario_3_regression.py (enhanced)

from nodes.common.review import security_review_node

def create_regression_scenario(config):
    f = flow()

    # ... existing regression nodes ...

    # Add security review for new code
    f.add(get_git_diff_node(), name="get_new_changes")
    f.add(security_review_node(), name="security_check")

    # Fail gate if critical security issues found
    f.add(call_llm_node(), name="gate_decision", params={
        "prompt_file": "prompts/regression_with_security.prompt.md"
    })

    return f
```

---

## Reusability Matrix

Shows which review nodes can be used across scenarios:

| Node | Scenario 2<br>Adaptation | Scenario 3<br>Regression | Scenario 4<br>Arch Drift | Scenario 6<br>Code Review |
|------|-------------------------|-------------------------|-------------------------|--------------------------|
| `get_git_diff_node` | - | Yes | Yes | Yes |
| `security_review_node` | Yes | Yes | - | Yes |
| `performance_review_node` | - | Yes | Yes | Yes |
| `quality_review_node` | Yes | Yes | - | Yes |
| `constraint_validation_node` | Yes | - | - | Yes |
| `test_coverage_review_node` | - | Yes | - | Yes |

**Key Insight**: Review nodes become **reusable building blocks** across multiple scenarios!

---

## Benefits of Node-based Architecture

### For Development

1. **Modularity**: Each review phase is independent
2. **Testability**: Test nodes in isolation
3. **Reusability**: Use nodes across scenarios
4. **Flexibility**: Mix and match review phases

### For Maintenance

1. **Easier to debug**: Isolate issues to specific nodes
2. **Simpler to extend**: Add new review types without touching others
3. **Clear responsibilities**: Each node has single purpose
4. **Better logging**: Track execution per node

### For Customization

1. **Selectable phases**: Run only needed reviews
2. **Configurable rules**: Per-node configuration
3. **Custom workflows**: Build scenario variants
4. **A/B testing**: Compare different node implementations

---

## Migration Path

### Step 1: Extract Core Logic

```python
# Before: code_review_agent/analyzers/security_analyzer.py
class SecurityAnalyzer:
    def analyze(self, code_lines):
        # Analysis logic
        return findings

# After: nodes/common/review/security_review_node.py
def security_review_node():
    def prep(ctx, params):
        return {
            "code_context": ctx.get("code_context"),
            "rules": ctx.get("constraint_rules", {}).get("security", {})
        }

    def exec(prep_result, params):
        # Reuse SecurityAnalyzer logic
        analyzer = SecurityAnalyzer()
        findings = analyzer.analyze(prep_result["code_context"])
        return {"findings": findings}

    def post(ctx, prep_result, exec_result, params):
        ctx["security_findings"] = exec_result["findings"]
        return "security_complete"

    return node(prep=prep, exec=exec, post=post)
```

### Step 2: Build Flow

```python
# scenarios/scenario_6_code_review.py
def create_code_review_scenario(config):
    f = flow()
    # ... add all nodes ...
    return f
```

### Step 3: Add CLI Integration

```python
# cli.py
@cli.command(name='code-review')
@click.option('--diff', help='Path to diff file')
@click.option('--git-diff', is_flag=True, help='Use git diff')
def code_review(diff, git_diff):
    """Scenario 6: Comprehensive code review"""
    # ...
```

---

## Architectural Principles

### 1. Single Responsibility
Each node does **one thing well**:
- `security_review_node` → Only security checks
- `performance_review_node` → Only performance checks

### 2. Composability
Build complex workflows from simple nodes:
```python
security_only = [get_diff, parse, security, report]
full_review = [get_diff, parse, *all_review_nodes*, aggregate, report]
```

### 3. Configurability
Each node accepts parameters:
```python
f.add(security_review_node(), name="security", params={
    "check_types": ["sql_injection", "xss"],
    "severity_threshold": "medium"
})
```

### 4. Context Sharing
Nodes communicate via shared context:
```python
# Node 1 writes
ctx["parsed_diff"] = diff_data

# Node 2 reads
diff_data = ctx.get("parsed_diff")
```

---

## Conclusion

**CodeReviewAgent's 7-phase pipeline maps perfectly to the Node/Scenario architecture.**

### Key Mappings

1. **Analyzers** → **Nodes**
   - Each analyzer becomes a node with prep/exec/post phases

2. **Pipeline Phases** → **Flow Sequence**
   - Linear pipeline becomes ordered node additions to flow

3. **Configuration** → **Node Parameters**
   - Constraint rules become node parameters

4. **Report Generation** → **Output Nodes**
   - Final formatting is dedicated output nodes

### Recommended Approach

Use the **Hybrid Model** (Option 3 from integration_analysis.md):
- Create modular review nodes in `nodes/common/review/`
- Build Scenario 6 as full code review pipeline
- Reuse review nodes across other scenarios
- Maintain flexibility for custom workflows

This gives you the best of both worlds: the comprehensive review capabilities of CodeReviewAgent and the flexibility of repoAnalysis's Flow/Node architecture.
