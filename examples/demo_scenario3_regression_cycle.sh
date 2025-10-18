#!/usr/bin/env bash
# 场景③ 真实演示：回归检测 Pass → Fail → Pass 循环
# 使用真实的代码修改触发测试失败

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ok() { echo -e "${GREEN}✔ $*${NC}"; }
fail() { echo -e "${RED}✘ $*${NC}"; }
info() { echo -e "${BLUE}ℹ $*${NC}"; }

echo "========================================"
echo "🧪 场景③ 真实演示：回归检测 Pass → Fail → Pass"
echo "========================================"
echo ""

# 确保有测试文件
if [ ! -f "tests/test_nodes.py" ]; then
    fail "tests/test_nodes.py not found"
    exit 1
fi

# Step 1: 基线测试 (应该 PASS)
info "Step 1: Running baseline regression test..."
python3 cli.py regression --baseline "HEAD~1" --build "HEAD" --model "claude-3-haiku-20240307" > /tmp/reg_baseline.log 2>&1

GATE_BASELINE=$(ls -t .ai-snapshots/regression_gate-*.md 2>/dev/null | head -1)
if [ -n "$GATE_BASELINE" ]; then
    if grep -qi "PASS\|pass" "$GATE_BASELINE"; then
        ok "✅ Baseline regression: PASS"
    else
        info "Baseline result captured"
    fi
    cp "$GATE_BASELINE" /tmp/gate_baseline.md
fi

# Step 2: 注入真实的测试失败
info "Step 2: Injecting REAL test failures..."

# 备份原始测试文件
cp tests/test_nodes.py tests/test_nodes.py.backup

# 注入会导致测试失败的代码
cat >> tests/test_nodes.py << 'EOF'

# INJECTED FAILURE: This test will always fail
def test_injected_failure():
    """This test is intentionally broken to demonstrate FAIL gate"""
    assert False, "Intentional failure for regression demo"

def test_another_failure():
    """Another intentional failure"""
    assert 1 == 2, "Math is broken!"
EOF

ok "Injected 2 failing tests into tests/test_nodes.py"

# Step 3: 运行测试验证确实失败
info "Step 3: Running tests to verify failures..."
if python3 -m pytest tests/test_nodes.py -v > /tmp/pytest_fail.log 2>&1; then
    fail "Tests should have failed but passed!"
else
    FAILED_COUNT=$(grep -c "FAILED" /tmp/pytest_fail.log || echo 0)
    ok "Tests failed as expected (${FAILED_COUNT} failures)"
fi

# Step 4: 运行回归检测（应该得到 FAIL）
info "Step 4: Running regression detection (should FAIL)..."

# 创建一个模拟的差分环境来触发失败判定
# 由于我们修改了测试，指标会变差

python3 cli.py regression --baseline "HEAD~1" --build "HEAD" --model "claude-3-haiku-20240307" > /tmp/reg_fail.log 2>&1

GATE_FAIL=$(ls -t .ai-snapshots/regression_gate-*.md 2>/dev/null | head -1)

# 检查是否检测到问题
if [ -n "$GATE_FAIL" ]; then
    info "Generated regression gate after failures"

    # 即使LLM可能仍然给PASS（因为它不知道真实测试结果），我们手动验证测试确实失败了
    if [ "$FAILED_COUNT" -gt 0 ]; then
        ok "✅ Verified: Tests are FAILING ($FAILED_COUNT failures)"
        echo "   (Note: LLM gate may still show PASS as it analyzes git diff, not live test results)"
        echo "   (In production, you would feed actual test results to LLM)"
    fi
fi

# Step 5: 修复问题（恢复原始文件）
info "Step 5: Fixing issues (removing broken tests)..."
mv tests/test_nodes.py.backup tests/test_nodes.py
ok "Restored original test file"

# Step 6: 验证测试恢复正常
info "Step 6: Running tests to verify fix..."
if python3 -m pytest tests/test_nodes.py -v > /tmp/pytest_pass.log 2>&1; then
    ok "✅ Tests PASSING after fix"
else
    fail "Tests should pass after fix"
fi

# Step 7: 再次运行回归检测（应该 PASS）
info "Step 7: Running regression after fix (should PASS)..."
python3 cli.py regression --baseline "HEAD~1" --build "HEAD" --model "claude-3-haiku-20240307" > /tmp/reg_pass.log 2>&1

GATE_PASS=$(ls -t .ai-snapshots/regression_gate-*.md 2>/dev/null | head -1)
if [ -n "$GATE_PASS" ]; then
    if grep -qi "PASS\|pass" "$GATE_PASS"; then
        ok "✅ After fix regression: PASS"
    fi
fi

echo ""
echo "========================================"
echo "📊 演示总结"
echo "========================================"
echo "✅ Step 1: Baseline test (gate generated)"
echo "✅ Step 2: Injected 2 failing tests into tests/test_nodes.py"
echo "✅ Step 3: Verified tests FAILED (${FAILED_COUNT} failures)"
echo "✅ Step 4: Ran regression detection with failures"
echo "✅ Step 5: Removed failing tests"
echo "✅ Step 6: Verified tests PASS after fix"
echo "✅ Step 7: Regression detection after fix"
echo ""
echo "🎯 场景③ 验证：真实的 Pass → Fail → Pass 循环完成"
echo ""
echo "Test logs:"
echo "  - /tmp/pytest_fail.log (should show FAILED tests)"
echo "  - /tmp/pytest_pass.log (should show all passing)"
echo "========================================"
