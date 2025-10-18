#!/bin/bash
# Demo: Scenario 6 - Code Review Pipeline

set -e

echo "=========================================="
echo "Scenario 6: Code Review Pipeline Demo"
echo "=========================================="
echo ""

# Create a test directory with vulnerable code
TEST_DIR="test_code_review_demo"
mkdir -p $TEST_DIR

echo "Creating test files with known issues..."

# Create a file with various issues
cat > $TEST_DIR/vulnerable_app.py << 'EOF'
# Example application with security, quality, and performance issues

import os
import subprocess

# Hardcoded secrets (SECURITY ISSUE)
API_KEY = "sk-1234567890abcdefghijklmnopqrstuvwxyz"
DATABASE_PASSWORD = "admin123"

def get_user_data(user_id):
    """Fetch user data from database"""

    # SQL Injection vulnerability (SECURITY ISSUE)
    query = f"SELECT * FROM users WHERE id={user_id}"
    cursor.execute(query)

    # Print statement instead of logging (QUALITY ISSUE)
    print(f"Fetching user: {user_id}")

    return cursor.fetchone()


def process_file(filename):
    """Process a file"""

    # Command injection vulnerability (SECURITY ISSUE)
    subprocess.run(f"cat {filename}", shell=True)

    # Path traversal vulnerability (SECURITY ISSUE)
    with open("../../../" + filename) as f:
        data = f.read()

    return data


def calculate_stats(data_list):
    """Calculate statistics"""

    # Nested loops - quadratic complexity (PERFORMANCE ISSUE)
    results = []
    for i in range(len(data_list)):
        for j in range(len(data_list)):
            if i != j:
                results.append(data_list[i] + data_list[j])

    # String concatenation in loop (PERFORMANCE ISSUE)
    output = ""
    for item in results:
        output += str(item) + ","

    return output


def long_function_example():
    # No docstring (QUALITY ISSUE)

    # Magic numbers (QUALITY ISSUE)
    timeout = 300
    max_retries = 5
    buffer_size = 8192

    # Deep nesting (QUALITY ISSUE)
    if timeout > 0:
        if max_retries > 0:
            if buffer_size > 0:
                if timeout < 1000:
                    print("Configuration OK")

    # Broad exception handler (QUALITY ISSUE)
    try:
        risky_operation()
    except:
        pass

    return True


# Weak cryptography (SECURITY ISSUE)
import hashlib
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()


# eval usage (SECURITY ISSUE)
def dynamic_execute(code_string):
    result = eval(code_string)
    return result
EOF

echo "Created vulnerable_app.py with multiple issues"
echo ""

# Initialize git repo
cd $TEST_DIR
git init > /dev/null 2>&1
git add .
git commit -m "Initial commit with vulnerable code" > /dev/null 2>&1

echo "Initialized git repository"
echo ""
echo "=========================================="
echo "Test 1: Full Code Review (all checks)"
echo "=========================================="
echo ""

cd ..
python cli.py code-review \
    --git-ref $TEST_DIR \
    --output $TEST_DIR/full_review.yaml \
    --format yaml

echo ""
echo "=========================================="
echo "Test 2: Security-Only Review"
echo "=========================================="
echo ""

python cli.py code-review \
    --git-ref $TEST_DIR \
    --security-only \
    --format markdown

echo ""
echo "=========================================="
echo "Test 3: Review Specific Diff File"
echo "=========================================="
echo ""

# Create a diff file
cat > $TEST_DIR/changes.patch << 'EOF'
diff --git a/new_feature.py b/new_feature.py
new file mode 100644
index 0000000..abcdefg
--- /dev/null
+++ b/new_feature.py
@@ -0,0 +1,15 @@
+def new_feature(user_input):
+    # New code with issues
+
+    # SQL injection
+    query = f"SELECT * FROM data WHERE name='{user_input}'"
+    execute(query)
+
+    # Hardcoded token
+    TOKEN = "ghp_1234567890abcdefghijklmnopqr"
+
+    # Print statement
+    print("Processing:", user_input)
+
+    # Magic number
+    limit = 999
EOF

python cli.py code-review \
    --diff $TEST_DIR/changes.patch \
    --output $TEST_DIR/diff_review.json \
    --format json

echo ""
echo "=========================================="
echo "Test 4: Run Python Test Suite"
echo "=========================================="
echo ""

echo "Running pytest on scenario 6 tests..."
python -m pytest tests/test_scenario_6_code_review.py -v --tb=short || true

echo ""
echo "=========================================="
echo "Demo Complete!"
echo "=========================================="
echo ""
echo "Generated files:"
echo "  - $TEST_DIR/vulnerable_app.py (test file with issues)"
echo "  - $TEST_DIR/full_review.yaml (full review report)"
echo "  - $TEST_DIR/diff_review.json (diff review report)"
echo ""
echo "Review the reports to see detected issues:"
echo "  cat $TEST_DIR/full_review.yaml"
echo "  cat $TEST_DIR/diff_review.json"
echo ""
echo "Cleanup:"
echo "  rm -rf $TEST_DIR"
echo ""
echo "=========================================="
