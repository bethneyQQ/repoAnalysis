#!/usr/bin/env bash
# 🎯 四场景完整验证框架 - 一键运行所有测试并验证成功/失败状态

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ok() { echo -e "${GREEN}✔ $*${NC}"; }
fail() { echo -e "${RED}✘ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠ $*${NC}"; }
info() { echo -e "${BLUE}ℹ $*${NC}"; }

# 检查环境
check_env() {
    info "检查运行环境..."

    if [ ! -f "$PROJECT_ROOT/cli.py" ]; then
        fail "未找到 cli.py，请在项目根目录运行"
        exit 1
    fi

    if ! command -v python &>/dev/null && ! command -v python3 &>/dev/null; then
        fail "需要 python 或 python3"
        exit 1
    fi

    PYTHON=$(command -v python3 || command -v python)

    if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
        warn "ANTHROPIC_API_KEY 未设置，将使用 Mock 模式"
        USE_REAL_LLM=false
    else
        ok "ANTHROPIC_API_KEY 已设置"
        USE_REAL_LLM=true
    fi
}

# 清理之前的测试文件
clean_previous() {
    info "清理之前的测试文件..."
    rm -rf "$PROJECT_ROOT/.ai-snapshots" 2>/dev/null || true
    mkdir -p "$PROJECT_ROOT/.ai-snapshots"
    ok "清理完成"
}

# 场景①：本地快照与回滚
test_scenario_1() {
    echo ""
    echo "========================================"
    echo "🔍 场景①：本地快照与回滚"
    echo "========================================"

    cd "$PROJECT_ROOT"

    # Step 1: 创建第一个快照
    info "Step 1: 创建初始快照..."
    $PYTHON cli.py snapshot --patterns "**/*.py" --model "claude-3-haiku-20240307" >/tmp/snap1.log 2>&1

    SNAP_COUNT=$(find .ai-snapshots -name "snapshot-*.md" 2>/dev/null | wc -l)
    if [ "$SNAP_COUNT" -gt 0 ]; then
        ok "快照创建成功 (共 $SNAP_COUNT 个)"
    else
        fail "快照创建失败"
        return 1
    fi

    # Step 2: 验证快照内容
    info "Step 2: 验证快照内容..."
    LATEST_SNAP=$(find .ai-snapshots -name "snapshot-*.md" 2>/dev/null | sort -r | head -1)

    if grep -q "代码健康体检\|风险\|snapshot_meta" "$LATEST_SNAP"; then
        ok "快照包含 AI 分析内容"
    else
        warn "快照可能使用了 Mock 模式"
    fi

    if grep -q "yaml\|risk_level\|themes" "$LATEST_SNAP"; then
        ok "快照包含 YAML 元数据"
    else
        fail "快照缺少 YAML 元数据"
        return 1
    fi

    # Step 3: 验证 LLM 使用
    if [ "$USE_REAL_LLM" = true ]; then
        if grep -q "\[Mock\|Mock LLM" "$LATEST_SNAP"; then
            fail "❌ 检测到 Mock 输出，未使用真实 LLM！"
            return 1
        else
            ok "✅ 确认使用了真实 LLM API"
        fi
    fi

    info "最新快照: $LATEST_SNAP"
    echo ""
    ok "场景① 验证完成"
    return 0
}

# 场景②：开源项目理解与组织化改造
test_scenario_2() {
    echo ""
    echo "========================================"
    echo "🔧 场景②：开源项目理解与组织化改造"
    echo "========================================"

    cd "$PROJECT_ROOT"

    # 提示：这个场景需要克隆仓库，较慢
    read -p "场景② 需要克隆 GitHub 仓库（约1-2分钟），是否继续？[y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        warn "跳过场景②"
        return 0
    fi

    # Step 1: 运行适配分析
    info "Step 1: 分析开源项目（克隆 + 分析）..."
    $PYTHON cli.py adapt "https://github.com/pallets/click" --model "claude-3-haiku-20240307" >/tmp/adapt.log 2>&1

    # Step 2: 检查输出
    PLAN_FILE=$(find .ai-snapshots -name "repo_adapt_plan-*.md" 2>/dev/null | sort -r | head -1)

    if [ -z "$PLAN_FILE" ]; then
        fail "未生成改造计划文件"
        return 1
    fi

    ok "改造计划已生成: $PLAN_FILE"

    # Step 3: 验证计划内容
    info "Step 2: 验证计划内容..."

    if grep -q "仓库理解.*要点" "$PLAN_FILE"; then
        ok "包含仓库理解要点"
    else
        fail "缺少仓库理解要点"
        return 1
    fi

    if grep -q "plan:" "$PLAN_FILE"; then
        ok "包含 plan YAML"
    else
        fail "缺少 plan YAML"
        return 1
    fi

    if grep -q "steps:\|changes:" "$PLAN_FILE"; then
        ok "包含可执行步骤"
    else
        fail "缺少可执行步骤"
        return 1
    fi

    # Step 4: 验证 LLM 使用
    if [ "$USE_REAL_LLM" = true ]; then
        if grep -q "\[Mock" "$PLAN_FILE"; then
            fail "检测到 Mock 输出"
            return 1
        else
            ok "确认使用了真实 LLM"
        fi
    fi

    echo ""
    ok "场景② 验证完成"
    return 0
}

# 场景③：回归检测与质量门禁
test_scenario_3() {
    echo ""
    echo "========================================"
    echo "🧪 场景③：回归检测与质量门禁"
    echo "========================================"

    cd "$PROJECT_ROOT"

    # Step 1: 运行回归检测
    info "Step 1: 收集指标并运行回归检测..."
    $PYTHON cli.py regression --baseline "HEAD~1" --build "HEAD" --model "claude-3-haiku-20240307" >/tmp/regression.log 2>&1

    # Step 2: 检查输出
    GATE_FILE=$(find .ai-snapshots -name "regression_gate-*.md" 2>/dev/null | sort -r | head -1)

    if [ -z "$GATE_FILE" ]; then
        fail "未生成门禁结果文件"
        return 1
    fi

    ok "门禁结果已生成: $GATE_FILE"

    # Step 3: 验证门禁判定
    info "Step 2: 验证门禁判定..."

    if grep -qi "PASS\|FAIL\|通过\|失败" "$GATE_FILE"; then
        ok "包含明确的 PASS/FAIL 判定"
    else
        fail "缺少 PASS/FAIL 判定"
        return 1
    fi

    if grep -q "gate:" "$GATE_FILE"; then
        ok "包含 gate YAML"
    else
        fail "缺少 gate YAML"
        return 1
    fi

    if grep -qi "overall:\|reasons:\|actions:" "$GATE_FILE"; then
        ok "gate YAML 包含必要字段"
    else
        fail "gate YAML 缺少必要字段"
        return 1
    fi

    # Step 4: 打印判定结果
    if grep -qi "PASS\|通过" "$GATE_FILE"; then
        ok "门禁判定: ✅ PASS"
    elif grep -qi "FAIL\|失败" "$GATE_FILE"; then
        warn "门禁判定: ❌ FAIL"
    fi

    # Step 5: 验证 LLM 使用
    if [ "$USE_REAL_LLM" = true ]; then
        if grep -q "\[Mock" "$GATE_FILE"; then
            fail "检测到 Mock 输出"
            return 1
        else
            ok "确认使用了真实 LLM"
        fi
    fi

    echo ""
    ok "场景③ 验证完成"
    return 0
}

# 场景④：架构影响与漂移扫描
test_scenario_4() {
    echo ""
    echo "========================================"
    echo "🏗️  场景④：架构影响与漂移扫描"
    echo "========================================"

    cd "$PROJECT_ROOT"

    # Step 1: 运行架构扫描
    info "Step 1: 分析依赖图和架构..."
    $PYTHON cli.py arch-drift --model "claude-3-haiku-20240307" >/tmp/arch.log 2>&1

    # Step 2: 检查输出
    ARCH_FILE=$(find .ai-snapshots -name "arch_gate-*.md" 2>/dev/null | sort -r | head -1)

    if [ -z "$ARCH_FILE" ]; then
        fail "未生成架构门禁文件"
        return 1
    fi

    ok "架构门禁已生成: $ARCH_FILE"

    # Step 3: 验证架构评分
    info "Step 2: 验证架构评分..."

    if grep -qiE "score.*[0-9]+|评分|分数" "$ARCH_FILE"; then
        SCORE=$(grep -oiE "score[: ]*[0-9]+" "$ARCH_FILE" | grep -oE "[0-9]+" | head -1)
        ok "架构评分: ${SCORE:-N/A}/100"
    else
        warn "未找到架构评分"
    fi

    if grep -qiE "risk.*level|风险.*等级" "$ARCH_FILE"; then
        ok "包含风险等级评估"
    fi

    # Step 4: 验证 arch_gate YAML
    if grep -q "arch_gate:" "$ARCH_FILE"; then
        ok "包含 arch_gate YAML"
    else
        fail "缺少 arch_gate YAML"
        return 1
    fi

    if grep -qiE "pass:.*true|pass:.*false" "$ARCH_FILE"; then
        ok "arch_gate 包含 pass 判定"
    else
        fail "arch_gate 缺少 pass 判定"
        return 1
    fi

    # Step 5: 打印判定结果
    if grep -qiE "pass:.*true|PASS|通过" "$ARCH_FILE"; then
        ok "架构门禁: ✅ PASS"
    elif grep -qiE "pass:.*false|FAIL|失败" "$ARCH_FILE"; then
        warn "架构门禁: ❌ FAIL"
    fi

    # Step 6: 验证 LLM 使用
    if [ "$USE_REAL_LLM" = true ]; then
        if grep -q "\[Mock" "$ARCH_FILE"; then
            fail "检测到 Mock 输出"
            return 1
        else
            ok "确认使用了真实 LLM"
        fi
    fi

    echo ""
    ok "场景④ 验证完成"
    return 0
}

# 生成测试报告
generate_report() {
    echo ""
    echo "========================================"
    echo "📊 生成测试报告"
    echo "========================================"

    cd "$PROJECT_ROOT"

    REPORT_FILE=".ai-snapshots/VERIFICATION_REPORT.md"

    cat > "$REPORT_FILE" << 'EOF'
# 🎯 四场景验证报告

## 执行时间
EOF

    date >> "$REPORT_FILE"

    cat >> "$REPORT_FILE" << EOF

## 环境信息
- Python: $($PYTHON --version)
- 项目路径: $PROJECT_ROOT
- LLM 模式: $([ "$USE_REAL_LLM" = true ] && echo "真实 API" || echo "Mock 模式")

## 生成的文件
EOF

    echo '```' >> "$REPORT_FILE"
    ls -lh .ai-snapshots/ >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"

    echo "" >> "$REPORT_FILE"
    echo "## 验证结果" >> "$REPORT_FILE"
    echo "- 场景① 本地快照: ${SCENARIO_1_STATUS:-未运行}" >> "$REPORT_FILE"
    echo "- 场景② 开源项目改造: ${SCENARIO_2_STATUS:-未运行}" >> "$REPORT_FILE"
    echo "- 场景③ 回归检测: ${SCENARIO_3_STATUS:-未运行}" >> "$REPORT_FILE"
    echo "- 场景④ 架构漂移: ${SCENARIO_4_STATUS:-未运行}" >> "$REPORT_FILE"

    ok "报告已生成: $REPORT_FILE"
}

# 主函数
main() {
    echo "========================================"
    echo "🚀 四场景完整验证框架"
    echo "========================================"
    echo ""

    check_env
    clean_previous

    # 运行所有场景
    if test_scenario_1; then
        SCENARIO_1_STATUS="✅ PASS"
    else
        SCENARIO_1_STATUS="❌ FAIL"
    fi

    if test_scenario_2; then
        SCENARIO_2_STATUS="✅ PASS"
    else
        SCENARIO_2_STATUS="❌ FAIL (或跳过)"
    fi

    if test_scenario_3; then
        SCENARIO_3_STATUS="✅ PASS"
    else
        SCENARIO_3_STATUS="❌ FAIL"
    fi

    if test_scenario_4; then
        SCENARIO_4_STATUS="✅ PASS"
    else
        SCENARIO_4_STATUS="❌ FAIL"
    fi

    # 生成报告
    generate_report

    # 总结
    echo ""
    echo "========================================"
    echo "📋 验证总结"
    echo "========================================"
    echo "场景① 本地快照: $SCENARIO_1_STATUS"
    echo "场景② 开源项目改造: $SCENARIO_2_STATUS"
    echo "场景③ 回归检测: $SCENARIO_3_STATUS"
    echo "场景④ 架构漂移: $SCENARIO_4_STATUS"
    echo ""
    echo "详细报告: .ai-snapshots/VERIFICATION_REPORT.md"
    echo "========================================"
}

main "$@"
