#!/usr/bin/env bash
# 场景③：回归检测与质量门禁实验

set -euo pipefail
source "$(dirname "$0")/common.sh"

echo "================================================"
echo "场景③：回归检测与质量门禁"
echo "================================================"

# 参数
BASELINE="${1:-HEAD~1}"
BUILD="${2:-HEAD}"

echo "📊 基线: $BASELINE"
echo "📊 构建: $BUILD"
echo ""

# 运行回归检测命令
$PYTHON cli.py regression --baseline "$BASELINE" --build "$BUILD" | tee /tmp/reg.out

# 检查输出
if grep -E "gate:|overall:|PASS|FAIL|门禁" /tmp/reg.out >/dev/null; then
    ok "门禁结果已输出"

    # 判断是否通过
    if grep -E "PASS|通过" /tmp/reg.out >/dev/null; then
        ok "✅ 门禁通过"
    elif grep -E "FAIL|失败|阻断" /tmp/reg.out >/dev/null; then
        warn "❌ 门禁失败"
    fi
elif grep -E "✅|已保存" /tmp/reg.out >/dev/null; then
    ok "命令执行成功"
else
    warn "命令已执行，请检查输出"
fi

# 检查门禁文件
if [ -d ".ai-snapshots" ]; then
    GATE_COUNT=$(find .ai-snapshots -name "regression_gate-*.md" 2>/dev/null | wc -l)
    if [ "$GATE_COUNT" -gt 0 ]; then
        ok "找到 $GATE_COUNT 个门禁结果文件"
        # 显示最新的门禁文件
        LATEST=$(find .ai-snapshots -name "regression_gate-*.md" 2>/dev/null | sort -r | head -1)
        if [ -n "$LATEST" ]; then
            echo ""
            echo "🚦 最新门禁: $LATEST"
            echo "--- 内容 ---"
            cat "$LATEST"
            echo "--- (完) ---"
        fi
    fi
fi

ok "场景③ 实验完成"
