# Integration Analysis: CodeReviewAgent & repoAnalysis

## Repository Overview

### CodeReviewAgent
**Purpose**: Comprehensive, constraint-based code review agent

**7-Phase Review Pipeline**:
1. Triage - Classify change type and risk level
2. Semantic Review - Logic, behavior, edge cases
3. Security Review - 8+ vulnerability categories
4. Performance Review - N+1 queries, algorithms, memory
5. Code Quality Review - 18+ quality patterns
6. Constraint Validation - Coding standards enforcement
7. Test & Docs Review - Coverage and documentation gaps

**Key Features**:
- 40+ constraint checks (security, quality, performance)
- Customizable forbidden patterns
- Naming convention enforcement
- Built with PocketFlow framework

### repoAnalysis (Current Repo)
**Purpose**: AI-powered code analysis with pluggable Flow/Node architecture

**5 Core Scenarios**:
1. Local Snapshot & Rollback
2. Repository Adaptation
3. Regression Detection & Quality Gate
4. Architecture Drift Scanning
5. Local RAG (Files-to-Prompt)

**Key Features**:
- Flow/Node pluggable architecture
- LLM-powered analysis (Claude, OpenAI)
- Complete Pass ↔ Fail ↔ Pass verification cycles

---

## Abstraction Strategy

### Option 1: CodeReviewAgent as Scenario 6

Integrate the entire 7-phase review pipeline as a new scenario.

#### Node Decomposition

##### Common Nodes (Reusable)

1. **`get_git_diff_node`**
   ```python
   # Extracts git diff or reads patch file
   - Input: git_ref, diff_file_path
   - Output: diff_content, changed_files
   ```

2. **`parse_diff_node`**
   ```python
   # Parses diff into structured format
   - Input: diff_content
   - Output: file_changes (added/removed/modified lines)
   ```

3. **`extract_code_context_node`**
   ```python
   # Extracts surrounding code for context
   - Input: changed_files, file_changes
   - Output: code_context_per_file
   ```

4. **`load_constraints_node`**
   ```python
   # Loads project-specific constraints
   - Input: rules_file, forbidden_patterns
   - Output: constraint_rules
   ```

5. **`triage_changes_node`**
   ```python
   # Classifies change type and risk level
   - Input: file_changes, code_context
   - Output: change_type, risk_level, priority_files
   ```

6. **`semantic_review_node`**
   ```python
   # Analyzes logic and behavior changes
   - Input: code_context, file_changes
   - Output: semantic_issues (logic flaws, edge cases)
   ```

7. **`security_review_node`**
   ```python
   # Detects security vulnerabilities
   - Input: code_context, constraint_rules
   - Output: security_issues (SQL injection, XSS, etc.)
   ```

8. **`performance_review_node`**
   ```python
   # Identifies performance issues
   - Input: code_context, file_changes
   - Output: performance_issues (N+1, complexity, memory)
   ```

9. **`quality_review_node`**
   ```python
   # Checks code quality patterns
   - Input: code_context, constraint_rules
   - Output: quality_issues (magic numbers, nesting, etc.)
   ```

10. **`constraint_validation_node`**
    ```python
    # Enforces coding standards
    - Input: code_context, constraint_rules
    - Output: constraint_violations
    ```

11. **`test_coverage_review_node`**
    ```python
    # Identifies missing tests
    - Input: file_changes, test_files
    - Output: test_gaps, coverage_issues
    ```

12. **`documentation_review_node`**
    ```python
    # Checks documentation completeness
    - Input: code_context, file_changes
    - Output: doc_gaps, missing_docstrings
    ```

13. **`aggregate_findings_node`**
    ```python
    # Aggregates all review findings
    - Input: semantic_issues, security_issues, performance_issues, etc.
    - Output: aggregated_findings (sorted by severity)
    ```

14. **`format_review_report_node`**
    ```python
    # Formats final review report
    - Input: aggregated_findings, diff_content
    - Output: review_report (YAML/JSON/MD)
    ```

##### Custom Nodes (Project-Specific)

15. **`check_naming_convention_node`** (already exists)
    - Can be reused for constraint validation

---

### Scenario 6: Code Review Pipeline

```python
# scenarios/scenario_6_code_review.py

from engine import flow
from nodes.common import (
    get_git_diff_node,
    parse_diff_node,
    extract_code_context_node,
    load_constraints_node,
    triage_changes_node,
    semantic_review_node,
    security_review_node,
    performance_review_node,
    quality_review_node,
    constraint_validation_node,
    test_coverage_review_node,
    documentation_review_node,
    aggregate_findings_node,
    format_review_report_node,
    call_llm_node
)

def create_code_review_scenario(config):
    """7-phase code review pipeline"""
    f = flow()

    # Phase 0: Preparation
    f.add(get_git_diff_node(), name="get_diff", params={
        "git_ref": config.get("git_ref", "HEAD"),
        "diff_file": config.get("diff_file")
    })

    f.add(parse_diff_node(), name="parse_diff")

    f.add(extract_code_context_node(), name="extract_context")

    f.add(load_constraints_node(), name="load_constraints", params={
        "rules_file": config.get("rules_file", "docs/code_review_rules.yaml")
    })

    # Phase 1: Triage
    f.add(triage_changes_node(), name="triage")

    # Phase 2: Semantic Review
    f.add(semantic_review_node(), name="semantic_review")

    # Phase 3: Security Review
    f.add(security_review_node(), name="security_review")

    # Phase 4: Performance Review
    f.add(performance_review_node(), name="performance_review")

    # Phase 5: Quality Review
    f.add(quality_review_node(), name="quality_review")

    # Phase 6: Constraint Validation
    f.add(constraint_validation_node(), name="constraint_validation")

    # Phase 7: Test & Docs Review
    f.add(test_coverage_review_node(), name="test_review")
    f.add(documentation_review_node(), name="doc_review")

    # Aggregation & Reporting
    f.add(aggregate_findings_node(), name="aggregate")

    f.add(call_llm_node(), name="llm_summary", params={
        "prompt_file": "prompts/code_review_summary.prompt.md",
        "model": config.get("model", "claude-3-haiku-20240307")
    })

    f.add(format_review_report_node(), name="format_report", params={
        "output_format": config.get("output_format", "yaml")
    })

    return f
```

---

### CLI Integration

```bash
# Review current git changes
python cli.py code-review --git-diff

# Review a specific diff file
python cli.py code-review --diff changes.patch

# With custom constraints
python cli.py code-review --git-diff --rules docs/custom_rules.yaml

# Output to file
python cli.py code-review --diff changes.patch --output review.yaml
```

---

## Option 2: Modular Integration

Instead of a single scenario, integrate review capabilities as **reusable building blocks**.

### Approach

1. **Create review-specific nodes** in `nodes/common/review/`
   - `security_scan_node.py`
   - `performance_scan_node.py`
   - `quality_scan_node.py`
   - etc.

2. **Use in multiple scenarios**:
   - Scenario 2 (Adaptation) → Use quality_scan to check org standards
   - Scenario 3 (Regression) → Use security_scan for new vulnerabilities
   - Scenario 4 (Arch Drift) → Use performance_scan for degradation
   - Scenario 6 (Code Review) → Use all review nodes

### Example: Security Scan in Regression Scenario

```python
# scenarios/scenario_3_regression.py

from nodes.common.review import security_scan_node

def create_regression_scenario(config):
    f = flow()

    # ... existing nodes ...

    # Add security scan for new code
    f.add(security_scan_node(), name="security_scan", params={
        "scan_types": ["sql_injection", "xss", "hardcoded_secrets"]
    })

    # ... rest of scenario ...

    return f
```

---

## Option 3: Hybrid Approach (Recommended)

Combine both approaches for maximum flexibility.

### Structure

```
nodes/
├── common/
│   ├── diff/                    # Diff-related nodes
│   │   ├── get_git_diff_node.py
│   │   ├── parse_diff_node.py
│   │   └── extract_code_context_node.py
│   ├── review/                  # Review nodes (reusable)
│   │   ├── security_scan_node.py
│   │   ├── performance_scan_node.py
│   │   ├── quality_scan_node.py
│   │   ├── constraint_validator_node.py
│   │   └── test_coverage_node.py
│   └── reporting/               # Report generation
│       ├── aggregate_findings_node.py
│       └── format_report_node.py
│
scenarios/
├── scenario_6_code_review.py   # Full 7-phase pipeline
└── scenario_7_pr_gate.py        # Lightweight PR check
```

### Benefits

1. **Modularity**: Review nodes can be used across scenarios
2. **Flexibility**: Mix and match review phases
3. **Maintainability**: Clear separation of concerns
4. **Extensibility**: Easy to add new review types

---

## Implementation Roadmap

### Phase 1: Core Review Nodes (Week 1)
- [ ] `get_git_diff_node`
- [ ] `parse_diff_node`
- [ ] `security_scan_node`
- [ ] `quality_scan_node`
- [ ] `aggregate_findings_node`

### Phase 2: Full Review Pipeline (Week 2)
- [ ] `performance_scan_node`
- [ ] `constraint_validator_node`
- [ ] `test_coverage_node`
- [ ] `documentation_review_node`
- [ ] Scenario 6: Code Review

### Phase 3: Integration (Week 3)
- [ ] Enhance Scenario 3 with security scan
- [ ] Enhance Scenario 4 with performance scan
- [ ] CLI integration
- [ ] Demo scripts

### Phase 4: Advanced Features (Week 4)
- [ ] GitHub/GitLab PR integration
- [ ] Custom constraint DSL
- [ ] Interactive review UI
- [ ] CI/CD pipeline integration

---

## Constraint Configuration

### Example: `docs/code_review_rules.yaml`

```yaml
security:
  sql_injection:
    enabled: true
    severity: critical
    patterns:
      - 'execute\s*\(\s*["\'].*%'
      - 'cursor\.execute\s*\(\s*f["\']'

  hardcoded_secrets:
    enabled: true
    severity: high
    patterns:
      - 'API_KEY\s*=\s*["\'][^"\']{20,}'
      - 'password\s*=\s*["\'](?!{{)'

performance:
  n_plus_one:
    enabled: true
    severity: medium
    check_orm_queries: true

  quadratic_complexity:
    enabled: true
    max_nested_loops: 2

quality:
  magic_numbers:
    enabled: true
    allowed_numbers: [0, 1, -1, 100]

  max_function_lines:
    enabled: true
    threshold: 50

  deep_nesting:
    enabled: true
    max_depth: 3

project:
  forbidden_patterns:
    - pattern: 'eval\s*\('
      message: 'eval() is forbidden for security reasons'
    - pattern: 'exec\s*\('
      message: 'exec() is forbidden for security reasons'

  naming_conventions:
    classes: PascalCase
    functions: snake_case
    constants: UPPER_SNAKE_CASE
```

---

## Benefits of Integration

### For CodeReviewAgent
- Gains Flow/Node architecture benefits
- Easier to extend and customize
- Better integration with other scenarios
- Reusable components across projects

### For repoAnalysis
- Adds comprehensive code review capabilities
- Enhances existing scenarios with review nodes
- Creates Scenario 6: Full code review pipeline
- Provides building blocks for custom workflows

---

## Next Steps

1. **Validate approach** with team/stakeholders
2. **Implement core nodes** (get_git_diff, parse_diff, security_scan)
3. **Create Scenario 6** with basic review pipeline
4. **Test with real PRs/diffs**
5. **Iterate and expand** review coverage
