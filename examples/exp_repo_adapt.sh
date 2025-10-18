#!/usr/bin/env bash
# 场景②：开源项目组织化改造实验

set -euo pipefail
source "$(dirname "$0")/common.sh"

echo "================================================"
echo "场景②：开源项目理解与组织化改造"
echo "================================================"

# 使用一个轻量级的示例仓库
REPO_URL="${1:-https://github.com/pallets/flask}"

echo "📦 目标仓库: $REPO_URL"
echo ""

# 运行改造规划命令
$PYTHON cli.py adapt "$REPO_URL" | tee /tmp/adapt.out

# 检查输出
if grep -E "plan:|steps:|改造计划" /tmp/adapt.out >/dev/null; then
    ok "生成了改造计划"
elif grep -E "✅|已保存" /tmp/adapt.out >/dev/null; then
    ok "命令执行成功（已保存改造计划）"
else
    warn "命令已执行，请检查输出"
fi

# 检查计划文件
if [ -d ".ai-snapshots" ]; then
    PLAN_COUNT=$(find .ai-snapshots -name "repo_adapt_plan-*.md" 2>/dev/null | wc -l)
    if [ "$PLAN_COUNT" -gt 0 ]; then
        ok "找到 $PLAN_COUNT 个改造计划文件"
        # 显示最新的计划文件
        LATEST=$(find .ai-snapshots -name "repo_adapt_plan-*.md" 2>/dev/null | sort -r | head -1)
        if [ -n "$LATEST" ]; then
            echo ""
            echo "📋 最新计划: $LATEST"
            echo "--- 前30行 ---"
            head -30 "$LATEST"
            echo "--- (省略) ---"
        fi
    fi
fi

ok "场景② 实验完成"
