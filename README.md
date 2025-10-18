# Code Repository Analysis System

AI-powered code analysis framework based on pluggable Flow/Node architecture

## Features
-  Clear separation between Common and Custom Nodes
-  Truly pluggable Scenario system
-  6 core scenarios: Snapshot, Adaptation, Regression, Architecture Drift, Local RAG, Code Review
-  LLM-powered analysis (Anthropic Claude, OpenAI)
-  Support for parallel/async execution
-  Structured output with YAML metadata
-  **Complete Pass ↔ Fail ↔ Pass verification cycles**
-  **Lightweight RAG with files-to-prompt integration**
-  **NEW: Comprehensive code review with security, quality, and performance checks**

## Quick Start

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set up your API key
export ANTHROPIC_API_KEY="your-api-key-here"
```

### One-Click Verification

Run all four scenarios with complete Pass ↔ Fail ↔ Pass cycles:

```bash
bash examples/run_all_scenarios.sh
```

This will:
-  Verify all four scenarios end-to-end
-  Generate structured outputs (JSON + YAML + MD)

### Try Local RAG

Quick start with the lightweight RAG feature:

```bash
# Ask questions about the codebase
python cli.py rag --patterns "**/*.py" --query "How does this project work?" --cxml

# Generate documentation from tests
python cli.py rag --patterns "tests/**/*.py" --query "Generate API documentation" --format markdown

# Locate features
python cli.py rag --query "Where is the snapshot functionality implemented?" --line-numbers
```

### Try Code Review (New!)

Quick start with the new code review feature:

```bash
# Review current changes
python cli.py code-review --git-diff

# Review against specific commit
python cli.py code-review --git-ref HEAD~1 --output review.yaml

# Security-only scan
python cli.py code-review --git-diff --security-only
```

## Six Core Scenarios

### Scenario ① - Local Snapshot & Rollback

**Purpose**: Create AI-powered code snapshots and restore files byte-for-byte

#### Features
- File content + hash snapshot (SHA-256)
- LLM-powered code health analysis
- Byte-for-byte restoration with hash verification
- **Complete cycle**: Create → Modify → Snapshot → Rollback → Verify

#### Commands
```bash
# Create snapshot
python cli.py snapshot --patterns "**/*.py" --model "claude-3-haiku-20240307"

# List snapshots
python cli.py snapshot-list

# Restore from snapshot
python cli.py snapshot-restore 20250118_120000
```

#### Demo Script
```bash
bash examples/demo_scenario1_snapshot_rollback.sh
```

**Verification Points**:
-  Creates snapshot with file contents and hashes
-  LLM generates code health report
-  Modifies files and creates second snapshot
-  Restores from first snapshot
-  Hash verification passes (byte-for-byte match)

**Output Files**:
- `.ai-snapshots/snapshot-{timestamp}.json` - Full snapshot with file contents
- `.ai-snapshots/snapshot-{timestamp}.md` - LLM analysis report

---

### Scenario ② - Repository Adaptation

**Purpose**: Analyze open-source projects and generate organization-compliant adaptation plans

#### Features
- Clone and analyze real GitHub repositories
- Detect organization standard violations
- Generate executable YAML plans
- 10-point repository understanding

#### Commands
```bash
python cli.py adapt "https://github.com/pallets/click" --model "claude-3-haiku-20240307"
```

**Verification Points**:
-  Clones real repository (Click project)
-  Generates 10 understanding points
-  Detects rule violations
-  Creates executable `plan` YAML with steps

**Output Files**:
- `.ai-snapshots/repo_adapt_plan-{timestamp}.md`

---

### Scenario ③ - Regression Detection & Quality Gate

**Purpose**: AI-powered quality gate decisions based on test metrics

#### Features
- Collects test pass rate, coverage, lint metrics
- LLM evaluates PASS/FAIL with reasoning
- **Complete cycle**: Baseline PASS → Inject Failure → FAIL → Fix → PASS

#### Commands
```bash
python cli.py regression --baseline "HEAD~1" --build "HEAD" --model "claude-3-haiku-20240307"
```

#### Demo Script
```bash
bash examples/demo_scenario3_regression_cycle.sh
```

**Verification Points**:
-  Baseline test returns PASS
-  Simulates failure injection
-  After fix returns PASS
-  Generates `gate` YAML with reasons and actions

**Output Files**:
- `.ai-snapshots/regression_gate-{timestamp}.md`

---

### Scenario ④ - Architecture Drift Scanning

**Purpose**: Detect architecture violations and structural drift

#### Features
- Dependency graph analysis
- Layer violation detection
- Complexity metrics tracking
- **Complete cycle**: Baseline PASS → Inject Drift → FAIL → Fix → PASS

#### Commands
```bash
python cli.py arch-drift --model "claude-3-haiku-20240307"
```

#### Demo Script
```bash
bash examples/demo_scenario4_arch_drift_cycle.sh
```

**Verification Points**:
-  Baseline returns PASS with score (e.g., 90/100)
-  Simulates architecture drift
-  After fix returns PASS
-  Generates `arch_gate` YAML with score and pass/fail

**Output Files**:
- `.ai-snapshots/arch_gate-{timestamp}.md`

---

### Scenario ⑤ - Local RAG (Files-to-Prompt)

**Purpose**: Lightweight RAG for quick codebase understanding and Q&A

Inspired by [Simon Willison's files-to-prompt](https://github.com/simonw/files-to-prompt), this scenario formats code files into LLM-friendly prompts for rapid codebase analysis.

#### Features
- Quick project onboarding (seconds to understand architecture)
- Auto-generate documentation from tests/source
- Code navigation ("Where is JWT validation?")
- Optimized for long-context models (Claude XML format)

#### Commands
```bash
# Quick overview
python cli.py rag --patterns "**/*.py" --query "How does this project work?" --cxml

# Generate docs from tests
python cli.py rag --patterns "tests/**/*.py" --query "Generate API documentation" --format markdown

# Locate features with line numbers
python cli.py rag --query "Where is snapshot implemented?" --line-numbers

# Code review
python cli.py rag --patterns "nodes/**/*.py" --query "Review code quality"
```

#### Demo Script
```bash
bash examples/demo_scenario5_local_rag.sh
```

#### Use Cases
1. **Project Onboarding**: "What's the architecture? What are the core modules?"
2. **Documentation Generation**: Extract API docs from test cases
3. **Feature Location**: "Where is JWT validation implemented?"
4. **Code Review**: Quality analysis with specific focus areas

#### Format Options
- `--format xml`: Standard XML output
- `--format xml --cxml`: Compact XML (recommended for long context)
- `--format markdown`: Markdown code blocks
- `--line-numbers`: Include line numbers for precise location

**Output**: Direct LLM response to terminal (no files saved)

**Documentation**: See `docs/scenario_5_rag_usage.md` for detailed usage

---

### Scenario ⑥ - Code Review Pipeline

**Purpose**: Comprehensive code review for security, quality, and performance

Integrates CodeReviewAgent capabilities with modular review nodes for detecting issues across multiple categories.

#### Features
- **Security Review**: SQL injection, hardcoded secrets, command injection, path traversal, unsafe deserialization, weak cryptography
- **Quality Review**: Magic numbers, deep nesting, long functions, print statements, broad exceptions, missing docstrings
- **Performance Review**: Nested loops (O(n²)), string concatenation in loops, N+1 queries, loading all data
- **Flexible Execution**: Run all checks or individual categories (security-only mode)
- **Multiple Output Formats**: YAML, JSON, Markdown
- **Security Gate**: Auto-fail on critical issues

#### Commands
```bash
# Full review of working directory changes
python cli.py code-review --git-diff

# Review specific commit
python cli.py code-review --git-ref HEAD~1 --output review.yaml

# Review a diff file
python cli.py code-review --diff changes.patch --format markdown

# Security-only scan
python cli.py code-review --git-diff --security-only
```

#### Demo Script
```bash
bash examples/demo_scenario6_code_review.sh
```

#### Detection Capabilities
- **Security**: 6 categories, 20+ patterns (SQL injection, secrets, command injection, etc.)
- **Quality**: 6 categories (magic numbers, nesting, print statements, etc.)
- **Performance**: 6 categories (nested loops, N+1 queries, inefficient patterns)

#### Use Cases
1. **Pre-commit Review**: Catch issues before committing
2. **PR Review**: Automated code review for pull requests
3. **Security Audit**: Focus on security vulnerabilities only
4. **Continuous Improvement**: Track code quality trends

#### Reusable Building Blocks
Review nodes can be used in other scenarios:
```python
from nodes.common.review import security_review_node, quality_review_node
from engine import flow

# Add security check to any scenario
f = flow()
f.add(security_review_node(), name="security")
```

**Output**: Review report with findings, severity levels, and security gate status

**Documentation**: See `docs/integration_summary.md` and `SCENARIO_6_SUMMARY.md`

---

## Test Coverage Summary

**All requirements from 4-Scenario Verification Framework are covered with REAL implementations**:

Note: Scenarios ⑤ (Local RAG) and ⑥ (Code Review) are utility features that don't require Pass/Fail verification cycles.

### Scenario ① - Local Snapshot  
- [x] Create snapshot with file contents + SHA256 hashes
- [x] Modify files
- [x] Create second snapshot
- [x] Restore from snapshot
- [x] **Hash verification passes (byte-for-byte match)** 
- [x] Demo script: `examples/demo_scenario1_snapshot_rollback.sh`
- [x] **Real Implementation**: Files actually restored and verified

### Scenario ② - Repository Adaptation  
- [x] Clone real GitHub repository (Click project)
- [x] Generate repository profile with 10 understanding points
- [x] Detect organization rule violations
- [x] Generate executable `plan.yaml` with steps
- [x] **Parse and execute plan (dry run)** 
- [x] Demo script: `examples/demo_scenario2_adapt_apply.sh`
- [x] **Real Implementation**: `PlanExecutor` class supports move/dep_replace/rename/config

### Scenario ③ - Regression Detection 
- [x] Baseline test (PASS)
- [x] **REAL failure injection** (adds failing tests to `tests/test_nodes.py`) 
- [x] **Run pytest and verify FAILED** 
- [x] **Remove failing tests and verify PASS** 
- [x] **Complete Pass → Fail → Pass cycle** 
- [x] Demo script: `examples/demo_scenario3_regression_cycle.sh`
- [x] **Real Implementation**: Actually modifies test files and runs pytest

### Scenario ④ - Architecture Drift 
- [x] Baseline architecture scan (score: 90/100, PASS)
- [x] **REAL drift injection** (creates circular dependency: module_a ↔ module_b) 
- [x] **Run Python import and verify ImportError** 
- [x] **Remove circular dependency and verify fix** 
- [x] **Complete Pass → Fail → Pass cycle** 
- [x] Demo script: `examples/demo_scenario4_arch_drift_cycle.sh`
- [x] **Real Implementation**: Actually creates circular dependencies and detects import errors

### Scenario ⑤ - Local RAG
- [x] Files-to-prompt node implementation
- [x] XML and Markdown formatting
- [x] Integration with LLM for Q&A
- [x] CLI integration: `python cli.py rag`
- [x] Demo script: `examples/demo_scenario5_local_rag.sh`
- [x] **Real Implementation**: Lightweight RAG for codebase understanding

### Scenario ⑥ - Code Review Pipeline
- [x] Security review node (6 vulnerability categories)
- [x] Quality review node (6 quality checks)
- [x] Performance review node (6 performance patterns)
- [x] Diff parsing and aggregation
- [x] Multiple output formats (YAML/JSON/Markdown)
- [x] CLI integration: `python cli.py code-review`
- [x] Test suite: 8 passing tests
- [x] Demo script: `examples/demo_scenario6_code_review.sh`
- [x] **Real Implementation**: Comprehensive code review with security gate

### One-Click Verification
- [x] Unified `run_all_scenarios.sh` script
- [x] Runs all scenarios sequentially with REAL implementations
- [x] Reports PASS/FAIL for each
- [x] **Execution time ≤ 10 minutes**

## Project Structure
```
repo-analysis/
├── nodes/                # Node definitions
│   ├── common/           # Reusable nodes
│   │   ├── get_files_node.py
│   │   ├── parse_code_node.py
│   │   ├── call_llm_node.py
│   │   ├── snapshot_files_node.py     # File snapshot with hashes
│   │   ├── save_snapshot_node.py      # Save JSON + MD snapshots
│   │   ├── write_file_node.py         # Write files to disk
│   │   ├── files_to_prompt_node.py    # Files-to-Prompt RAG
│   │   ├── diff/                      # NEW: Diff processing
│   │   │   ├── get_git_diff_node.py
│   │   │   └── parse_diff_node.py
│   │   └── review/                    # NEW: Code review
│   │       ├── security_review_node.py
│   │       ├── quality_review_node.py
│   │       ├── performance_review_node.py
│   │       └── aggregate_findings_node.py
│   └── custom/           # Organization-specific nodes
├── scenarios/            # Scenario implementations
│   ├── scenario_1_local_snapshot.py   # With rollback support
│   ├── scenario_2_repo_adapt.py
│   ├── scenario_3_regression.py
│   ├── scenario_4_arch_drift.py
│   ├── scenario_5_local_rag.py        # Local RAG
│   └── scenario_6_code_review.py      # NEW: Code Review Pipeline
├── prompts/              # LLM prompt templates
│   ├── snapshot.prompt.md
│   ├── repo_adapt.prompt.md
│   ├── regression.prompt.md
│   ├── arch_drift.prompt.md
│   └── rag_query.prompt.md            # RAG query template
├── examples/             # Demo scripts
│   ├── demo_scenario1_snapshot_rollback.sh
│   ├── demo_scenario3_regression_cycle.sh
│   ├── demo_scenario4_arch_drift_cycle.sh
│   ├── demo_scenario5_local_rag.sh    # RAG demo
│   ├── demo_scenario6_code_review.sh  # NEW: Code Review demo
│   └── run_all_scenarios.sh
├── utils/                # Utility functions
│   ├── llm_client.py     # LLM API wrapper with logging
│   └── ast_parser.py     # Code parsing
├── docs/                 # Documentation
│   ├── org_rules.yaml               # Organization standards
│   ├── scenario_5_rag_usage.md      # RAG usage guide
│   ├── integration_summary.md       # NEW: Code Review integration
│   ├── integration_analysis.md      # NEW: Detailed analysis
│   ├── architecture_comparison.md   # NEW: Architecture guide
│   └── implementation_example.md    # NEW: Implementation examples
├── engine.py             # Flow/Node execution engine
├── cli.py                # CLI with 6 scenarios
├── requirements.txt      # Dependencies
```

## CLI Commands

### Snapshot Commands
```bash
# Create snapshot
python cli.py snapshot --patterns "**/*.py" --model "claude-3-haiku-20240307"

# List all snapshots
python cli.py snapshot-list

# Restore from snapshot (with hash verification)
python cli.py snapshot-restore <snapshot-id>
```

### Analysis Commands
```bash
# Repository adaptation
python cli.py adapt "https://github.com/pallets/click" --model "claude-3-haiku-20240307"

# Regression detection
python cli.py regression --baseline "HEAD~1" --build "HEAD" --model "claude-3-haiku-20240307"

# Architecture drift
python cli.py arch-drift --model "claude-3-haiku-20240307"
```

### RAG Commands
```bash
# Quick project overview
python cli.py rag --patterns "**/*.py" --query "How does this project work?" --cxml

# Generate documentation from tests
python cli.py rag --patterns "tests/**/*.py" --query "Generate API documentation" --format markdown

# Locate feature implementation
python cli.py rag --query "Where is snapshot functionality implemented?" --line-numbers

# Multiple patterns
python cli.py rag --patterns "**/*.py" --patterns "**/*.md" --query "Summarize the project"

# Code review
python cli.py rag --patterns "nodes/**/*.py" --query "Review error handling and code reuse"
```

### Code Review Commands (New!)
```bash
# Review current working directory changes
python cli.py code-review --git-diff

# Review against specific commit
python cli.py code-review --git-ref HEAD~1 --output review.yaml

# Review a diff/patch file
python cli.py code-review --diff changes.patch --format markdown

# Security-only scan (fast)
python cli.py code-review --git-diff --security-only

# Full review with JSON output
python cli.py code-review --git-ref main --format json --output report.json
```

## How It Works

### Flow/Node Architecture
Each scenario is a **Flow** composed of **Nodes**:
```python
def create_local_snapshot_scenario(config):
    f = flow()
    f.add(get_files_node(), name="get_files")
    f.add(parse_code_node(), name="parse_code")
    f.add(snapshot_files_node(), name="snapshot_files")  # Saves file contents + hashes
    f.add(call_llm_node(), name="llm_snapshot", params={
        "prompt_file": "prompts/snapshot.prompt.md",
        "model": config.get("model", "gpt-4"),
    })
    f.add(save_snapshot_node(), name="save_snapshot")  # Saves JSON + MD
    return f
```

### Three-Phase Node Execution
Each node has three phases:
1. **prep**: Prepare parameters from context
2. **exec**: Execute the operation
3. **post**: Update context and determine next state

### Example: Local RAG Flow
```python
from engine import flow
from nodes.common import get_files_node, files_to_prompt_node, call_llm_node

def create_rag_scenario(config):
    f = flow()

    # Step 1: Get files matching patterns
    f.add(get_files_node(), name="get_files", params={
        "patterns": config.get("patterns", ["**/*.py"])
    })

    # Step 2: Format files for LLM (files-to-prompt style)
    f.add(files_to_prompt_node(), name="format", params={
        "format": "xml",
        "cxml": True,  # Compact XML for long context
        "include_line_numbers": False
    })

    # Step 3: Query LLM
    f.add(call_llm_node(), name="query", params={
        "prompt_file": "prompts/rag_query.prompt.md",
        "model": "claude-3-haiku-20240307"
    })

    return f

# Run the flow
result = create_rag_scenario(config).run({
    "project_root": ".",
    "query": "How does this work?"
})
print(result.get("llm_response"))
```

## Requirements

- Python 3.7+
- anthropic (for Claude API)
- openai (for OpenAI API)
- click (for CLI)
- pyyaml (for config parsing)
- gitpython (for git operations)

## Related Documentation

### Scenario 6 Resources
- [SCENARIO_6_SUMMARY.md](SCENARIO_6_SUMMARY.md) - Complete implementation summary
- [Integration Summary](docs/integration_summary.md) - Overview and design decisions
- [Integration Analysis](docs/integration_analysis.md) - Detailed analysis and options
- [Architecture Comparison](docs/architecture_comparison.md) - CodeReviewAgent vs Node-based
- [Implementation Example](docs/implementation_example.md) - Working code examples

### Tests
- All scenario 6 tests: `python -m pytest tests/test_scenario_6_code_review.py -v`
- Individual node tests available in test file
- 8 passing test cases covering security, quality, performance, and integration

## Contributing

Contributions welcome! Areas for improvement:
- Additional language support beyond Python
- LLM-powered semantic review for Scenario 6
- CI/CD pipeline integration (GitHub Actions, GitLab CI)
- Custom reporting formats and templates
- More review patterns and rules
- Integration with issue trackers

## Related Projects

- [CodeReviewAgent](https://github.com/bethneyQQ/CodeReviewAgent) - Constraint-based code review agent (can be integrated as Scenario 6)

## License

MIT

