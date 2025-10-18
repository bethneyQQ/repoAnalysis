#!/usr/bin/env bash
# 一键运行所有四个场景的完整验证
# 演示「成功 ↔ 失败 ↔ 修复成功」完整闭环

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

ok() { echo -e "${GREEN}✔ $*${NC}"; }
fail() { echo -e "${RED}✘ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠ $*${NC}"; }
info() { echo -e "${BLUE}ℹ $*${NC}"; }
header() { echo -e "${CYAN}$*${NC}"; }

echo ""
header "╔════════════════════════════════════════════════════════════╗"
header "║      🎯 四场景完整验证框架 - 一键运行所有测试              ║"
header "╚════════════════════════════════════════════════════════════╝"
echo ""

# 检查环境
info "Checking environment..."

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    warn "ANTHROPIC_API_KEY not set - using Mock mode"
    USE_REAL_LLM=false
else
    ok "ANTHROPIC_API_KEY is set"
    USE_REAL_LLM=true
fi

if [ ! -f "cli.py" ]; then
    fail "cli.py not found! Please run from project root"
    exit 1
fi

ok "Environment check passed"
echo ""

# 清理旧的快照
info "Cleaning previous snapshots..."
mkdir -p .ai-snapshots
rm -f .ai-snapshots/*.json .ai-snapshots/*.md 2>/dev/null || true
ok "Cleaned"
echo ""

# 场景计数
PASSED=0
FAILED=0
TOTAL=4

START_TIME=$(date +%s)

# ========================================
# 场景① - 本地快照与回滚
# ========================================
header "┌────────────────────────────────────────────────────────────┐"
header "│ 场景① : 本地快照与回滚                                      │"
header "└────────────────────────────────────────────────────────────┘"
echo ""

if bash "$SCRIPT_DIR/demo_scenario1_snapshot_rollback.sh" > /tmp/scenario1.log 2>&1; then
    ok "场景① PASSED - Snapshot and rollback working"
    ((PASSED++))
else
    fail "场景① FAILED"
    ((FAILED++))
    echo "Check /tmp/scenario1.log for details"
fi
echo ""

# ========================================
# 场景② - 开源项目理解与组织化改造
# ========================================
header "┌────────────────────────────────────────────────────────────┐"
header "│ 场景② : 开源项目理解与组织化改造                            │"
header "└────────────────────────────────────────────────────────────┘"
echo ""

info "Running repository adaptation (this may take 1-2 minutes)..."
if python3 cli.py adapt "https://github.com/pallets/click" --model "claude-3-haiku-20240307" > /tmp/scenario2.log 2>&1; then
    PLAN_FILE=$(find .ai-snapshots -name "repo_adapt_plan-*.md" 2>/dev/null | head -1)
    if [ -n "$PLAN_FILE" ] && grep -q "plan:" "$PLAN_FILE"; then
        ok "场景② PASSED - Repository analysis and plan generation working"
        ((PASSED++))
    else
        fail "场景② FAILED - Plan file missing or invalid"
        ((FAILED++))
    fi
else
    fail "场景② FAILED"
    ((FAILED++))
fi
echo ""

# ========================================
# 场景③ - 回归检测与质量门禁
# ========================================
header "┌────────────────────────────────────────────────────────────┐"
header "│ 场景③ : 回归检测与质量门禁 (Pass ↔ Fail ↔ Pass)            │"
header "└────────────────────────────────────────────────────────────┘"
echo ""

if bash "$SCRIPT_DIR/demo_scenario3_regression_cycle.sh" > /tmp/scenario3.log 2>&1; then
    ok "场景③ PASSED - Regression detection working"
    ((PASSED++))
else
    fail "场景③ FAILED"
    ((FAILED++))
fi
echo ""

# ========================================
# 场景④ - 架构影响与漂移扫描
# ========================================
header "┌────────────────────────────────────────────────────────────┐"
header "│ 场景④ : 架构影响与漂移扫描 (Pass ↔ Fail ↔ Pass)            │"
header "└────────────────────────────────────────────────────────────┘"
echo ""

if bash "$SCRIPT_DIR/demo_scenario4_arch_drift_cycle.sh" > /tmp/scenario4.log 2>&1; then
    ok "场景④ PASSED - Architecture drift detection working"
    ((PASSED++))
else
    fail "场景④ FAILED"
    ((FAILED++))
fi
echo ""

# 计算执行时间
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

# ========================================
# 生成最终报告
# ========================================
header "╔════════════════════════════════════════════════════════════╗"
header "║                     📊 最终验证报告                         ║"
header "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "执行时间: ${MINUTES}m ${SECONDS}s"
echo "LLM 模式: $([ "$USE_REAL_LLM" = true ] && echo '真实 API' || echo 'Mock 模式')"
echo ""

echo "测试结果:"
echo "  ✅ PASSED: $PASSED/$TOTAL"
echo "  ❌ FAILED: $FAILED/$TOTAL"
echo ""

if [ $FAILED -eq 0 ]; then
    ok "🎉 所有场景验证通过！"
    echo ""
    echo "生成的文件:"
    ls -lh .ai-snapshots/ | tail -n +2
    echo ""
    exit 0
else
    fail "⚠️  部分场景验证失败"
    echo ""
    echo "检查日志文件:"
    echo "  - /tmp/scenario1.log"
    echo "  - /tmp/scenario2.log"
    echo "  - /tmp/scenario3.log"
    echo "  - /tmp/scenario4.log"
    echo ""
    exit 1
fi
