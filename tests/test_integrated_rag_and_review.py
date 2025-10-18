"""
Integrated test: Combining Local RAG with Code Review

This test demonstrates how to use Scenario 5 (RAG) and Scenario 6 (Code Review)
together for enhanced code understanding and review.
"""

import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine import flow
from nodes.common import get_files_node, files_to_prompt_node
from nodes.common.diff import get_git_diff_node, parse_diff_node
from nodes.common.review import security_review_node, quality_review_node, performance_review_node


def test_rag_enhanced_code_review():
    """
    Test combining RAG and Code Review for better context understanding

    Workflow:
    1. Use RAG to understand the codebase context
    2. Run code review on diff
    3. Use RAG results to provide better review context
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create a base file
        base_file = tmpdir / "auth.py"
        base_file.write_text("""
# Authentication module
def authenticate_user(username, password):
    '''Authenticate user with credentials'''
    # Existing secure implementation
    hashed_password = hash_with_salt(password)
    return verify_password(username, hashed_password)

def hash_with_salt(password):
    '''Hash password with salt'''
    import hashlib
    salt = generate_salt()
    return hashlib.sha256(salt + password.encode()).hexdigest()
""", encoding='utf-8')

        # Create a new file with issues
        new_file = tmpdir / "login.py"
        new_file.write_text("""
# Login module with security issues
def quick_login(user_id):
    # SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE id={user_id}"
    cursor.execute(query)

    # Reusing existing auth module (good practice)
    from auth import authenticate_user
    return authenticate_user(username, password)
""", encoding='utf-8')

        # Create diff
        diff_content = """diff --git a/login.py b/login.py
new file mode 100644
index 0000000..abcdefg
--- /dev/null
+++ b/login.py
@@ -0,0 +1,10 @@
+# Login module with security issues
+def quick_login(user_id):
+    # SQL Injection vulnerability
+    query = f"SELECT * FROM users WHERE id={user_id}"
+    cursor.execute(query)
+
+    # Reusing existing auth module (good practice)
+    from auth import authenticate_user
+    return authenticate_user(username, password)
"""
        diff_file = tmpdir / "changes.diff"
        diff_file.write_text(diff_content, encoding='utf-8')

        # ===== Phase 1: Use RAG to understand existing codebase =====
        print("\n" + "="*80)
        print("Phase 1: RAG Analysis - Understanding Existing Codebase")
        print("="*80)

        rag_flow = flow()
        rag_flow.add(get_files_node(), name="get_files", params={
            "patterns": ["auth.py"]
        })
        rag_flow.add(files_to_prompt_node(), name="format", params={
            "format": "markdown",
            "include_line_numbers": True
        })

        rag_result = rag_flow.run({"project_root": str(tmpdir)})

        assert "formatted_prompt" in rag_result
        formatted_code = rag_result["formatted_prompt"]

        print(f"✓ RAG analyzed {rag_result['files_to_prompt_stats']['files_processed']} files")
        print(f"✓ Generated {len(formatted_code)} characters of context")

        # Extract insights from RAG (in real scenario, would send to LLM)
        codebase_context = {
            "has_auth_module": "authenticate_user" in formatted_code,
            "uses_hashing": "hash_with_salt" in formatted_code,
            "security_aware": "sha256" in formatted_code
        }

        print("\nCodebase Insights from RAG:")
        print(f"  - Has authentication module: {codebase_context['has_auth_module']}")
        print(f"  - Uses password hashing: {codebase_context['uses_hashing']}")
        print(f"  - Security-aware codebase: {codebase_context['security_aware']}")

        # ===== Phase 2: Code Review with Context =====
        print("\n" + "="*80)
        print("Phase 2: Code Review - Analyzing New Changes")
        print("="*80)

        review_flow = flow()
        review_flow.add(get_git_diff_node(), name="get_diff", params={
            "diff_file": str(diff_file)
        })
        review_flow.add(parse_diff_node(), name="parse")
        review_flow.add(security_review_node(), name="security")
        review_flow.add(quality_review_node(), name="quality")

        review_result = review_flow.run({"project_root": str(tmpdir)})

        security_findings = review_result.get("security_findings", [])
        quality_findings = review_result.get("quality_findings", [])

        print(f"✓ Security issues found: {len(security_findings)}")
        print(f"✓ Quality issues found: {len(quality_findings)}")

        # ===== Phase 3: Enhanced Analysis =====
        print("\n" + "="*80)
        print("Phase 3: Context-Aware Analysis")
        print("="*80)

        # SQL injection should be detected
        sql_issues = [f for f in security_findings if f["type"] == "sql_injection"]
        assert len(sql_issues) > 0, "Should detect SQL injection"

        # Enhanced insight: Code reuses existing auth module (detected by RAG)
        if codebase_context["security_aware"]:
            print("\n✓ POSITIVE: New code imports from existing secure auth module")
            print("  → Good practice: Reusing secure authentication logic")

        # But still has SQL injection
        if sql_issues:
            print("\n✗ CRITICAL: SQL injection vulnerability detected")
            print(f"  → Found in: {sql_issues[0]['file']}:{sql_issues[0]['line']}")
            print(f"  → Issue: {sql_issues[0]['message']}")

        # Recommendation based on both RAG and Review
        print("\n" + "="*80)
        print("Context-Aware Recommendations:")
        print("="*80)
        print("1. SECURITY: Fix SQL injection - use parameterized queries")
        print("2. CONSISTENCY: Good that login.py reuses auth.py (detected via RAG)")
        print("3. PATTERN: Continue using the secure auth patterns from auth.py")

        # Assert combined insights
        assert codebase_context["has_auth_module"], "RAG should detect auth module"
        assert len(sql_issues) > 0, "Review should detect SQL injection"

        print("\n" + "="*80)
        print("✓ Integration Test Passed")
        print("="*80)


def test_rag_for_review_context():
    """
    Use RAG to provide context for understanding review findings

    Scenario: Review finds an issue, use RAG to understand if there's
    a better pattern already in the codebase
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Existing file with good practice
        good_file = tmpdir / "database.py"
        good_file.write_text("""
def safe_query(user_id):
    '''Safe database query using parameters'''
    query = "SELECT * FROM users WHERE id = ?"
    return cursor.execute(query, (user_id,))
""", encoding='utf-8')

        # New file with bad practice
        bad_file = tmpdir / "api.py"
        bad_file.write_text("""
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id={user_id}"
    return cursor.execute(query)
""", encoding='utf-8')

        # Step 1: Review finds issue
        review_flow = flow()
        review_flow.add(security_review_node(), name="security")

        review_result = review_flow.run({
            "code_context": {
                "api.py": bad_file.read_text().split('\n')
            }
        })

        security_issues = review_result["security_findings"]
        assert len(security_issues) > 0, "Should find SQL injection"

        # Step 2: Use RAG to find better patterns in codebase
        rag_flow = flow()
        rag_flow.add(get_files_node(), name="get_files", params={
            "patterns": ["database.py"]
        })
        rag_flow.add(files_to_prompt_node(), name="format")

        rag_result = rag_flow.run({"project_root": str(tmpdir)})

        formatted_context = rag_result["formatted_prompt"]

        # Step 3: Generate context-aware recommendation
        has_safe_pattern = "cursor.execute(query, (" in formatted_context

        if has_safe_pattern:
            recommendation = (
                f"Issue found: {security_issues[0]['message']}\n"
                f"Better pattern exists in database.py - use parameterized queries like:\n"
                f"  cursor.execute(query, (user_id,))"
            )
        else:
            recommendation = security_issues[0]['message']

        print("\n" + "="*80)
        print("Context-Aware Recommendation:")
        print("="*80)
        print(recommendation)
        print("="*80)

        assert has_safe_pattern, "RAG should find safe pattern in codebase"
        assert len(security_issues) > 0, "Review should find issue"


def test_diff_based_rag_review():
    """
    Test reviewing only the changed code using both RAG and Review

    This simulates a PR review workflow:
    1. Get diff of changes
    2. Parse diff to understand what changed
    3. Use RAG to understand surrounding context
    4. Run focused review on changed code
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create files
        file1 = tmpdir / "utils.py"
        file1.write_text("""
def process_data(data):
    for item in data:
        for record in item:
            result = expensive_operation(record)
    return result
""", encoding='utf-8')

        # Create diff
        diff_content = """diff --git a/utils.py b/utils.py
index 1234567..abcdefg 100644
--- a/utils.py
+++ b/utils.py
@@ -1,6 +1,8 @@
 def process_data(data):
+    # New nested loop - performance issue
     for item in data:
         for record in item:
+            for detail in record:
-            result = expensive_operation(record)
+                result = expensive_operation(detail)
     return result
"""
        diff_file = tmpdir / "changes.diff"
        diff_file.write_text(diff_content, encoding='utf-8')

        # Combined workflow
        combined_flow = flow()

        # Get and parse diff
        combined_flow.add(get_git_diff_node(), name="get_diff", params={
            "diff_file": str(diff_file)
        })
        combined_flow.add(parse_diff_node(), name="parse")

        # Review for performance issues
        combined_flow.add(performance_review_node(), name="performance")

        result = combined_flow.run({"project_root": str(tmpdir)})

        # Verify
        assert "parsed_diff" in result
        assert "performance_findings" in result

        findings = result["performance_findings"]

        # Should detect nested loops or performance issues
        print(f"\nFound {len(findings)} performance issues in diff")
        for finding in findings:
            print(f"  - {finding['type']}: {finding['message']}")

        assert len(findings) > 0, "Should find performance issues"


if __name__ == "__main__":
    print("Running integrated RAG + Code Review tests...\n")

    test_rag_enhanced_code_review()
    print("\n")

    test_rag_for_review_context()
    print("\n")

    test_diff_based_rag_review()
    print("\n")

    print("="*80)
    print("All integrated tests passed!")
    print("="*80)
